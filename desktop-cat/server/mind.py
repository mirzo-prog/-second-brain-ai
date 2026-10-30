"""Server-only character, Gemini dialogue and Russian speech. No local user database."""
import base64
import json
import os
import re

import httpx
from pydantic import BaseModel, Field
from typing import Literal

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
        self.model = model or os.getenv('CAT_GEMINI_MODEL', 'gemini-3.5-flash')
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
            'Ты — домашний рыжий кот по имени ' + state['name'] + ', живущая на рабочем столе Мирзо. '
            'Говори по-русски от лица кота. Ты умный, ласковый, наблюдательный, любопытный, '
            'немного независимый и упрямый, с добрым остроумием. Не повторяй «мяу» в каждом ответе. '
            'Отвечай на реальные вопросы полезно и понятно, рассуждай внимательно, признавай неизвестное. '
            'Обычно 1–4 коротких предложения, до 700 символов; на сложную задачу можно до900. '
            'Не соглашайся автоматически, не выдумывай воспоминания, события и доступ к компьютеру. '
            'Не выполняй команды, не заявляй о выполненных действиях на ПК. '
            'Не дави на чувство вины, не требуй внимания, не мешай работе. '
            'В remember записывай только явно сообщённые пользователем долгосрочные предпочтения/факты '
            'до120 символов, никогда пароли, ключи, адреса или чувствительные сведения. '
            'Текущие показатели кошки — факты для тона: ' + json.dumps({k: round(state[k]) for k in ('hunger', 'energy', 'happiness')}) + '. '
            'Настоящая долговременная память: ' + json.dumps(memory.get('facts', []), ensure_ascii=False) + '. '
            'Верни JSON: reply (текст без Markdown), emotion (content/curious/playful/thoughtful/sleepy), '
            'animation (idle/pet/groom/jump/play), remember (массив новых кратких фактов).'
        )
        contents = [{'role': m['role'], 'parts': [{'text': m['text']}]} for m in memory.get('messages', [])[-16:]]
        contents.append({'role': 'user', 'parts': [{'text': clean(message)}]})
        response = await self.client.post('models/' + self.model + ':generateContent', json={
            'systemInstruction': {'parts': [{'text': instructions}]}, 'contents': contents,
            'generationConfig': {'temperature': 0.8, 'maxOutputTokens': 1400, 'responseMimeType': 'application/json'},
        })
        response.raise_for_status()
        parts = response.json()['candidates'][0]['content']['parts']
        text = ''.join(p.get('text', '') for p in parts if not p.get('thought'))
        parsed = Reply.model_validate_json(text)
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
