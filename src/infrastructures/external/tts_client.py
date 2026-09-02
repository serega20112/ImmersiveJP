from __future__ import annotations

import os

import httpx


class TTSClient:
    def __init__(self) -> None:
        self.kokoro_api_key: str = os.getenv("KOKORO_API_KEY", "")
        self.kokoro_url: str = os.getenv("KOKORO_URL", "https://api.kokoro.ai/tts")
        self.kokoro_voice: str = os.getenv("KOKORO_VOICE", "ru-RU-Dmitry")
        self.freetts_api_key: str = os.getenv("FREETTS_API_KEY", "")
        self.freetts_url: str = os.getenv("FREETTS_URL", "https://api.freetts.com/tts")

    async def synthesize(self, text: str, lang: str = "ru") -> bytes:
        if self.kokoro_api_key:
            try:
                return await self._synthesize_kokoro(text, lang)
            except Exception:
                pass
        return await self._synthesize_freetts(text, lang)

    async def _synthesize_kokoro(self, text: str, lang: str) -> bytes:
        payload = {
            "text": text,
            "lang": lang,
            "voice": self.kokoro_voice,
            "format": "mp3",
        }
        headers = {"Content-Type": "application/json"}
        if self.kokoro_api_key:
            headers["Authorization"] = f"Bearer {self.kokoro_api_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.kokoro_url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.content

    async def _synthesize_freetts(self, text: str, lang: str) -> bytes:
        payload = {"text": text, "lang": lang}
        headers: dict[str, str] = {}
        if self.freetts_api_key:
            headers["Authorization"] = f"Bearer {self.freetts_api_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.freetts_url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.content
