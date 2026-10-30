"""Desktop cat API. Persistent pet state is private or authenticated-encrypted in remote GitHub storage.

No local SQLite/JSON fallback: misconfigured persistence is an error, not silent data loss.
"""
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import datetime, timezone
import asyncio
import base64
import hmac
import json
import os
from typing import Literal
from uuid import UUID

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from mind import GeminiMind, PERSONALITY, clean
from cryptography.fernet import Fernet, InvalidToken


def now():
    return datetime.now(timezone.utc).timestamp()


def initial_state(timestamp=None):
    timestamp = now() if timestamp is None else timestamp
    return {
        'schemaVersion': 1, 'revision': 1, 'name': 'Марсель',
        'createdAt': timestamp, 'updatedAt': timestamp,
        'hunger': 80.0, 'energy': 90.0, 'happiness': 85.0, 'affection': 0,
        'sleeping': False, 'lastAction': 'hello',
        'appearance': {'white': '#fffaf1', 'orange': '#ed8b3a', 'stripe': '#c96d29'},
        'settings': {'size': 1.0, 'speed': 46, 'roaming': True, 'visible': True, 'voiceEnabled': True},
        'recentRequests': [], 'personality': deepcopy(PERSONALITY),
        'memory': {'facts': [], 'messages': []},
    }


def evolve(state, timestamp=None):
    state = deepcopy(state)
    state.setdefault('personality', deepcopy(PERSONALITY))
    state.setdefault('memory', {'facts': [], 'messages': []})
    timestamp = now() if timestamp is None else timestamp
    hours = max(0, timestamp - state['updatedAt']) / 3600
    state['hunger'] = max(0.0, state['hunger'] - hours * 3)
    state['happiness'] = max(15.0, state['happiness'] - hours * 1.5)
    rate = 12 if state['sleeping'] else -2
    state['energy'] = max(5.0, min(100.0, state['energy'] + hours * rate))
    state['updatedAt'] = timestamp
    return state


def public_state(state, storage='remote-private-repository'):
    result = deepcopy(state)
    result.pop('recentRequests', None)
    result['serverTime'] = now()
    result['storage'] = storage
    return result


class Conflict(Exception):
    pass


class GitHubStore:
    def __init__(self, repository, token, branch='main', encryption_key=None):
        if len(repository.split('/')) != 2 or not token:
            raise ValueError('Configure CAT_STATE_REPOSITORY and CAT_GITHUB_TOKEN')
        self.repository = repository
        self.branch = branch
        encryption_key = encryption_key if encryption_key is not None else os.environ.get('CAT_STATE_ENCRYPTION_KEY', '')
        self.cipher = Fernet(encryption_key.encode()) if encryption_key else None
        self.storage_kind = 'remote-encrypted-repository' if self.cipher else 'remote-private-repository'
        self.is_private = False
        self.client = httpx.AsyncClient(
            base_url='https://api.github.com', timeout=20,
            headers={'Authorization': 'Bearer ' + token,
                     'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28'},
        )
        self.verified = False

    async def verify(self):
        response = await self.client.get('/repos/' + self.repository)
        response.raise_for_status()
        self.is_private = response.json().get('private') is True
        if not self.is_private and not self.cipher:
            raise ValueError('Cat state repository must be private or use authenticated encryption')
        self.verified = True

    async def load(self):
        if not self.verified:
            await self.verify()
        response = await self.client.get('/repos/' + self.repository + '/contents/pet.json',
                                         params={'ref': self.branch})
        if response.status_code == 404:
            return None, None
        response.raise_for_status()
        data = response.json()
        stored = json.loads(base64.b64decode(data['content']))
        if stored.get('encryption') == 'fernet':
            if not self.cipher:
                raise ValueError('State encryption key is missing')
            try:
                stored = json.loads(self.cipher.decrypt(stored['ciphertext'].encode()))
            except InvalidToken:
                raise ValueError('State authentication failed') from None
        elif not self.is_private:
            raise ValueError('Refusing unencrypted state in a public repository')
        return stored, data['sha']

    async def save(self, state, version):
        if not self.verified:
            await self.verify()
        raw = json.dumps(state, ensure_ascii=False).encode()
        if self.cipher:
            raw = json.dumps({'encryption': 'fernet', 'ciphertext': self.cipher.encrypt(raw).decode()}).encode()
        payload = {
            'message': 'Update desktop cat state', 'branch': self.branch,
            'content': base64.b64encode(raw).decode(),
        }
        if version:
            payload['sha'] = version
        response = await self.client.put('/repos/' + self.repository + '/contents/pet.json', json=payload)
        if response.status_code in (409, 422):
            raise Conflict()
        response.raise_for_status()
        return response.json()['content']['sha']

    async def close(self):
        await self.client.aclose()


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['pet', 'feed', 'play', 'sleep', 'wake']
    requestId: UUID


class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = Field(default=None, min_length=1, max_length=24)
    size: float | None = Field(default=None, ge=0.65, le=1.6)
    speed: int | None = Field(default=None, ge=15, le=100)
    roaming: bool | None = None
    visible: bool | None = None
    voiceEnabled: bool | None = None
    requestId: UUID


class Chat(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1, max_length=2000)
    requestId: UUID


class Speech(BaseModel):
    model_config = ConfigDict(extra='forbid')
    requestId: UUID


def create_app(store=None, token=None, mind=None):
    token = token if token is not None else os.environ.get('CAT_ACCESS_TOKEN', '')
    if len(token) < 24:
        raise ValueError('CAT_ACCESS_TOKEN must contain at least 24 characters')
    store = store if store is not None else GitHubStore(
        os.environ.get('CAT_STATE_REPOSITORY', ''), os.environ.get('CAT_GITHUB_TOKEN', ''),
        os.environ.get('CAT_STATE_BRANCH', 'main'))
    lock = asyncio.Lock()
    chat_lock = asyncio.Lock()
    speech_lock = asyncio.Lock()
    mind = mind if mind is not None else GeminiMind()
    speech_cache = {}
    cache = {'state': None, 'at': 0}

    def view_state(value):
        return public_state(value, getattr(store, 'storage_kind', 'remote-private-repository'))

    @asynccontextmanager
    async def lifespan(app):
        yield
        await store.close()
        await mind.close()

    app = FastAPI(title='Марсель · Desktop Cat', lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    def authorize(authorization):
        expected = 'Bearer ' + token
        if not hmac.compare_digest((authorization or '').encode(), expected.encode()):
            raise HTTPException(401, 'Authentication required')

    async def transaction(change=None, request_id=None):
        async with lock:
            if change is None and cache['state'] is not None and now() - cache['at'] < 30:
                return view_state(evolve(cache['state']))
            try:
                for attempt in range(3):
                    state, version = await store.load()
                    new = state is None
                    state = evolve(state or initial_state())
                    if request_id in state['recentRequests']:
                        return view_state(state)
                    if change:
                        change(state)
                        state['revision'] += 1
                        state['recentRequests'] = (state['recentRequests'] + [request_id])[-64:]
                    if change or new:
                        try:
                            await store.save(state, version)
                        except Conflict:
                            continue
                    cache.update(state=deepcopy(state), at=now())
                    return view_state(state)
                raise HTTPException(409, 'Concurrent update; retry with the same requestId')
            except (httpx.HTTPError, OSError, ValueError, KeyError):
                # Never return upstream URLs, credentials or remote error bodies.
                raise HTTPException(503, 'Remote pet storage unavailable') from None

    @app.middleware('http')
    async def no_cache(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'service': 'desktop-cat'}

    @app.get('/v1/pet')
    async def get_pet(authorization: str | None = Header(default=None)):
        authorize(authorization)
        state = await transaction()
        state['intelligenceAvailable'] = mind.available
        return state

    def find_reply(state, request_id):
        return next((m for m in reversed(state['memory']['messages'])
                     if m['role'] == 'model' and m.get('requestId') == request_id), None)

    @app.post('/v1/pet/chat')
    async def chat(body: Chat, authorization: str | None = Header(default=None)):
        authorize(authorization)
        message = clean(body.message.strip())
        if not message:
            raise HTTPException(422, 'Empty message')
        async with chat_lock:
            state = await transaction()
            request_id = str(body.requestId)
            answer = find_reply(state, request_id)
            if answer is None:
                try:
                    generated = await mind.reply(state, message)
                except (httpx.HTTPError, ValueError, KeyError, IndexError) as err:
                    import logging
                    logging.getLogger("desktop_cat.chat").error("Chat reply error: %s", err, exc_info=True)
                    raise HTTPException(503, 'Intelligence unavailable; dialogue has not been saved') from None

                def remember(current):
                    current['memory']['messages'] = (current['memory']['messages'] + [
                        {'role': 'user', 'text': message, 'requestId': request_id},
                        {'role': 'model', 'text': generated.reply, 'requestId': request_id,
                         'emotion': generated.emotion, 'animation': generated.animation},
                    ])[-24:]
                    facts = current['memory']['facts']
                    current['memory']['facts'] = list(dict.fromkeys(facts + generated.remember))[-20:]

                state = await transaction(remember, request_id)
                answer = find_reply(state, request_id)
            if answer is None:
                raise HTTPException(409, 'requestId was already used for another action')
            return {'pet': state, 'reply': answer['text'], 'emotion': answer['emotion'],
                    'animation': answer['animation'], 'requestId': request_id, 'voiceAvailable': mind.available}

    @app.post('/v1/pet/speech')
    async def speech(body: Speech, authorization: str | None = Header(default=None)):
        authorize(authorization)
        state = await transaction()
        request_id = str(body.requestId)
        answer = find_reply(state, request_id)
        if answer is None:
            raise HTTPException(404, 'Saved reply not found')
        async with speech_lock:
            cached = speech_cache.get(request_id)
            if cached and now() - cached[0] < 300:
                audio = cached[1]
            else:
                try:
                    audio = await mind.speak(answer['text'])
                except (httpx.HTTPError, ValueError, KeyError, IndexError):
                    raise HTTPException(503, 'Speech temporarily unavailable') from None
                speech_cache.clear()
                speech_cache[request_id] = (now(), audio)
            return {'wavBase64': audio, 'requestId': request_id}

    @app.post('/v1/pet/actions')
    async def action(body: Action, authorization: str | None = Header(default=None)):
        authorize(authorization)

        def change(state):
            action = body.action
            state['lastAction'] = action
            if action == 'feed':
                state['hunger'] = min(100, state['hunger'] + 22)
                state['happiness'] = min(100, state['happiness'] + 3)
            elif action == 'pet':
                state['affection'] += 1
                state['happiness'] = min(100, state['happiness'] + 5)
            elif action == 'play':
                state['sleeping'] = False
                state['happiness'] = min(100, state['happiness'] + 15)
                state['energy'] = max(5, state['energy'] - 8)
                state['hunger'] = max(0, state['hunger'] - 3)
            else:
                state['sleeping'] = action == 'sleep'

        return await transaction(change, str(body.requestId))

    @app.patch('/v1/pet/settings')
    async def settings(body: Settings, authorization: str | None = Header(default=None)):
        authorize(authorization)

        def change(state):
            values = body.model_dump(exclude_none=True, exclude={'requestId'})
            if 'name' in values:
                name = values.pop('name').strip()
                if not name:
                    raise HTTPException(422, 'Name must contain visible characters')
                state['name'] = name
            state['settings'].update(values)

        return await transaction(change, str(body.requestId))

    return app

