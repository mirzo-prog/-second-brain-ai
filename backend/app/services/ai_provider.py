import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import datetime

from app.core.config import settings
from app.models.entities import Setting, AIUsage

logger = logging.getLogger("second_brain.ai")

class AIServiceError(Exception):
    pass

class AIProvider:
    def __init__(self, db: Session):
        self.db = db
        self._load_config()

    def _load_config(self):
        settings_map = {s.key: s.value for s in self.db.query(Setting).all()}
        self.gemini_key = settings_map.get("gemini_api_key", "").strip()
        self.gemini_model = settings_map.get("gemini_model", "gemini-2.5-flash")
        self.ollama_url = settings_map.get("ollama_base_url", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = settings_map.get("ollama_model", "llama3:latest")
        self.active_provider = settings_map.get("active_provider", "gemini")

    def _log_usage(self, provider: str, model: str, tokens_in: int, tokens_out: int, request_type: str):
        try:
            record = AIUsage(
                provider=provider,
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                request_type=request_type
            )
            self.db.add(record)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to log AI usage: {e}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        request_type: str = "general"
    ) -> str:
        self._load_config()
        if self.active_provider == "ollama":
            return await self._call_ollama(prompt, system_instruction, temperature, request_type)
        else:
            return await self._call_gemini(prompt, system_instruction, temperature, request_type)

    async def generate_structured(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        request_type: str = "structured"
    ) -> Dict[str, Any]:
        self._load_config()
        if self.active_provider == "ollama":
            return await self._call_ollama_json(prompt, system_instruction, request_type)
        else:
            return await self._call_gemini_json(prompt, system_instruction, request_type)

    async def _call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        request_type: str
    ) -> str:
        if not self.gemini_key:
            raise AIServiceError(
                "API-ключ Google Gemini не настроен. Пожалуйста, укажите ваш ключ в разделе «Настройки»."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        
        body: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=body)
            except Exception as e:
                raise AIServiceError(f"Ошибка сети при обращении к Gemini API: {str(e)}")

        if response.status_code != 200:
            error_data = response.json().get("error", {})
            err_msg = error_data.get("message", response.text)
            raise AIServiceError(f"Ошибка Gemini API ({response.status_code}): {err_msg}")

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise AIServiceError("Модель не вернула ответ.")
        
        content_parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in content_parts)

        # Track usage
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        resp_tokens = usage.get("candidatesTokenCount", 0)
        self._log_usage("gemini", self.gemini_model, prompt_tokens, resp_tokens, request_type)

        return text

    async def _call_gemini_json(
        self,
        prompt: str,
        system_instruction: Optional[str],
        request_type: str
    ) -> Dict[str, Any]:
        if not self.gemini_key:
            raise AIServiceError(
                "API-ключ Google Gemini не настроен. Пожалуйста, укажите ваш ключ в разделе «Настройки»."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        
        body: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=body)
            except Exception as e:
                raise AIServiceError(f"Ошибка сети при обращении к Gemini API: {str(e)}")

        if response.status_code != 200:
            error_data = response.json().get("error", {})
            err_msg = error_data.get("message", response.text)
            raise AIServiceError(f"Ошибка Gemini API ({response.status_code}): {err_msg}")

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise AIServiceError("Модель не вернула структурированный ответ.")
        
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        usage = data.get("usageMetadata", {})
        self._log_usage(
            "gemini",
            self.gemini_model,
            usage.get("promptTokenCount", 0),
            usage.get("candidatesTokenCount", 0),
            request_type
        )

        try:
            return json.loads(text)
        except Exception:
            # Cleanup potential markdown wrapper if model added ```json
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            return json.loads(clean_text.strip())

    async def _call_ollama(
        self,
        prompt: str,
        system_instruction: Optional[str],
        temperature: float,
        request_type: str
    ) -> str:
        url = f"{self.ollama_url}/api/chat"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                response = await client.post(url, json=body)
            except Exception as e:
                raise AIServiceError(f"Не удалось подключиться к Ollama ({self.ollama_url}): {str(e)}")

        if response.status_code != 200:
            raise AIServiceError(f"Ошибка Ollama ({response.status_code}): {response.text}")

        data = response.json()
        resp_msg = data.get("message", {}).get("content", "")
        
        # Track usage
        prompt_eval = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)
        self._log_usage("ollama", self.ollama_model, prompt_eval, eval_count, request_type)

        return resp_msg

    async def _call_ollama_json(
        self,
        prompt: str,
        system_instruction: Optional[str],
        request_type: str
    ) -> Dict[str, Any]:
        url = f"{self.ollama_url}/api/chat"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction + "\nОтвет должен быть строго в формате JSON."})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2}
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            try:
                response = await client.post(url, json=body)
            except Exception as e:
                raise AIServiceError(f"Не удалось подключиться к Ollama ({self.ollama_url}): {str(e)}")

        if response.status_code != 200:
            raise AIServiceError(f"Ошибка Ollama ({response.status_code}): {response.text}")

        content = response.json().get("message", {}).get("content", "{}")
        try:
            return json.loads(content)
        except Exception as e:
            raise AIServiceError(f"Не удалось распарсить JSON от Ollama: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        self._load_config()
        if self.active_provider == "gemini":
            if not self.gemini_key:
                return {"success": False, "provider": "gemini", "message": "API ключ не задан"}
            try:
                res = await self.generate_text("Ответь одним словом: Работает", temperature=0.1, request_type="test")
                return {"success": True, "provider": "gemini", "model": self.gemini_model, "sample_response": res.strip()}
            except Exception as e:
                return {"success": False, "provider": "gemini", "message": str(e)}
        else:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{self.ollama_url}/api/tags")
                    if resp.status_code == 200:
                        models = [m.get("name") for m in resp.json().get("models", [])]
                        return {"success": True, "provider": "ollama", "url": self.ollama_url, "available_models": models}
                    return {"success": False, "provider": "ollama", "message": f"Код ответа: {resp.status_code}"}
            except Exception as e:
                return {"success": False, "provider": "ollama", "message": str(e)}
