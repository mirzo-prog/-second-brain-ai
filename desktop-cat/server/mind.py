"""Server-only character, Gemini dialogue and Russian speech. No local user database."""
import asyncio
import base64
import json
import logging
import os
import re

import httpx
from pydantic import BaseModel, Field
from typing import Literal

logger = logging.getLogger("desktop_cat.mind")

PERSONALITY = {
    'traits': ['ласковый', 'любопытный', 'сообразительный', 'немного упрямый', 'с мягким юмором'],
    'description': 'Любит разбираться в задачах и уютно сидеть рядом. Имеет собственные предпочтения, но уважает человека.',
}


class Reply(BaseModel):
    reply: str = Field(min_length=1, max_length=900)
    emotion: Literal['content', 'curious', 'playful', 'thoughtful', 'sleepy'] = 'content'
    animation: Literal['idle', 'pet', 'groom', 'jump', 'play'] = 'idle'
    remember: list[str] = Field(default_factory=list, max_length=4)


def clean(text):
    text = re.sub(r'\b(?:ghp_|rnd_|sk-)[A-Za-z0-9_-]{12,}\b', '[секрет скрыт]', text)
    return re.sub(r'(?i)\b(api_key|password|access_token|refresh_token)\s*[:=]\s*\S+', r'\1=[скрыто]', text)


class GeminiMind:
    def __init__(self, key=None, model=None, tts_model=None, transport=None):
        self.key = key if key is not None else os.getenv('CAT_GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ''))
        self.model = model or os.getenv('CAT_GEMINI_MODEL', 'gemini-3.5-flash-lite')
        self.tts_model = tts_model or os.getenv('CAT_TTS_MODEL', 'gemini-3.8-flash-lite-tts')
        self.client = httpx.AsyncClient(base_url='https://generativelanguage.googleapis.com/v1beta/',
                                       headers={'x-goog-api-key': self.key}, timeout=40, transport=transport)

    @property
    def available(self):
        return bool(self.key)

    async def reply(self, state, message):
        if not self.available:
            raise ValueError('Intelligence not configured')
        memory = state.get('memory', {})
        instructions = (
            'Ты — домашний рыжий кот по имени ' + state['name'] + ', живущий на рабочем столе Мирзо. '
            'Говори по-русски от лица кота. Ты умный, ласковый, наблюдательный, любопытный, '
            'немного независимый и упрямый, с добрым остроумием. Не повторяй «мяу» в каждом ответе. '
            'Отвечай на реальные вопросы полезно и понятно, рассуждай внимательно, признавай неизвестное. '
            'Обычно 1–4 коротких предложения, до 700 символов; на сложную задачу можно до 900. '
            'Не соглашайся автоматически, не выдумывай воспоминания, события и доступ к компьютеру. '
            'Не выполняй команды, не заявляй о выполненных действиях на ПК. '
            'Не дави на чувство вины, не требуй внимания, не мешай работе. '
            'В remember записывай только явно сообщённые пользователем долгосрочные предпочтения/факты '
            'до 120 символов, никогда пароли, ключи, адреса или чувствительные сведения. '
            'Текущие показатели кошки — факты для тона: ' + json.dumps({k: round(state[k]) for k in ('hunger', 'energy', 'happiness')}) + '. '
            'Настоящая долговременная память: ' + json.dumps(memory.get('facts', []), ensure_ascii=False) + '. '
            'Верни JSON: reply (текст без Markdown), emotion (content/curious/playful/thoughtful/sleepy), '
            'animation (idle/pet/groom/jump/play), remember (массив новых кратких фактов).'
        )

        # Normalize message sequence for Gemini: alternating user and model, starting with user
        raw_msgs = memory.get('messages', [])
        normalized = []
        for m in raw_msgs:
            role = 'user' if m.get('role') == 'user' else 'model'
            msg_text = clean(str(m.get('text', '')).strip())
            if not msg_text:
                continue
            if normalized and normalized[-1]['role'] == role:
                normalized[-1]['parts'][0]['text'] += "\n" + msg_text
            else:
                normalized.append({'role': role, 'parts': [{'text': msg_text}]})

        while normalized and normalized[0]['role'] != 'user':
            normalized.pop(0)

        normalized = normalized[-14:]
        while normalized and normalized[0]['role'] != 'user':
            normalized.pop(0)

        user_msg = clean(message)
        if normalized and normalized[-1]['role'] == 'user':
            normalized[-1]['parts'][0]['text'] += "\n" + user_msg
        else:
            normalized.append({'role': 'user', 'parts': [{'text': user_msg}]})

        body = {
            'systemInstruction': {'parts': [{'text': instructions}]},
            'contents': normalized,
            'generationConfig': {
                'temperature': 0.8,
                'maxOutputTokens': 1400,
                'responseMimeType': 'application/json'
            },
        }

        models_to_try = list(dict.fromkeys([self.model, 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-flash-lite-latest']))
        response = None
        last_err = None
        for current_model in models_to_try:
            for attempt in range(2):
                try:
                    response = await self.client.post('models/' + current_model + ':generateContent', json=body)
                    if response.status_code in (429, 503) and attempt == 0:
                        logger.warning("Gemini model %s transient %s, retrying after 1.5s", current_model, response.status_code)
                        await asyncio.sleep(1.5)
                        continue
                    if response.status_code in (404, 429, 503):
                        logger.warning("Gemini model %s returned %s, trying next fallback model", current_model, response.status_code)
                        break
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    last_err = e
                    if attempt == 0 and e.response.status_code in (429, 503):
                        logger.warning("Gemini model %s transient HTTP %s, retrying", current_model, e.response.status_code)
                        await asyncio.sleep(1.5)
                        continue
                    logger.warning("Gemini model %s failed: %s %s", current_model, e.response.status_code, e.response.text[:200])
                    break
                except Exception as e:
                    last_err = e
                    logger.warning("Gemini model %s failed with exception: %s", current_model, e)
                    break
            if response is not None and response.status_code == 200:
                break

        if response is None or response.status_code != 200:
            if last_err:
                raise last_err
            raise ValueError('All Gemini fallback models exhausted or unavailable')

        data = response.json()
        candidates = data.get('candidates', [])
        if not candidates:
            raise ValueError('Gemini returned no candidates')

        parts = candidates[0].get('content', {}).get('parts', [])
        text = ''.join(p.get('text', '') for p in parts if not p.get('thought')).strip()

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()

        try:
            parsed = Reply.model_validate_json(text)
        except Exception as parse_err:
            logger.warning("JSON parse failed on Gemini output: %s; falling back. Raw: %s", parse_err, text[:200])
            reply_match = re.search(r'"reply"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
            if reply_match:
                extracted = reply_match.group(1).encode().decode('unicode_escape', errors='ignore')
                parsed = Reply(reply=extracted, emotion='content', animation='idle', remember=[])
            else:
                clean_raw = re.sub(r'[\{\}\[\]"]', '', text).strip()
                parsed = Reply(reply=clean_raw[:800] or 'Мурр, я тебя слышу!', emotion='content', animation='idle', remember=[])

        parsed.reply = clean(parsed.reply)
        parsed.remember = [clean(f[:120]) for f in parsed.remember if f.strip()]
        return parsed

    async def speak(self, text):
        if not self.available:
            raise ValueError('Speech not configured')
        # Current Gemini TTS REST contract: transcript and style are separate.
        response = await self.client.post('interactions', json={
            'model': self.tts_model,
            'input': [{'type': 'user_input', 'content': [{'type': 'text', 'text': text[:900],
                'annotations': [{'type': 'speech_metadata',
                                 'style': 'Russian, warm and gently playful, calm conversational pace, soft natural female voice'}]}]}],
            'response_format': {'type': 'audio', 'mime_type': 'audio/wav'},
            'generation_config': {'speech_config': [{'voice': 'Kore'}]},
        })
        response.raise_for_status()
        audio = [c for step in response.json().get('steps', []) for c in step.get('content', []) if c.get('type') == 'audio']
        if not audio:
            raise ValueError('Missing generated speech')
        encoded = audio[-1]['data']
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > 4_000_000 or not raw.startswith(b'RIFF') or raw[8:12] != b'WAVE':
            raise ValueError('Unsupported speech payload')
        return encoded

    async def close(self):
        await self.client.aclose()
