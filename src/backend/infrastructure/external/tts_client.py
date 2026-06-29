from __future__ import annotations

import os
from typing import Optional

import httpx


class TTSClient:
    """Text-to-speech client with Kokoro as primary and FreeTTS as fallback.

    Supports Russian language synthesis with automatic fallback on errors.
    """

    def __init__(self):
        # Kokoro (primary)
        self.kokoro_api_key = os.getenv("KOKORO_API_KEY", "")
        self.kokoro_url = os.getenv("KOKORO_URL", "https://api.kokoro.ai/tts")
        self.kokoro_voice = os.getenv("KOKORO_VOICE", "ru-RU-Dmitry")

        # FreeTTS (fallback)
        self.freetts_api_key = os.getenv("FREETTS_API_KEY", "")
        self.freetts_url = os.getenv("FREETTS_URL", "https://api.freetts.com/tts")

    async def synthesize(self, text: str, lang: str = "ru") -> bytes:
        """Synthesize text to speech.

        Tries Kokoro first, falls back to FreeTTS on failure.

        Args:
            text: Text to synthesize
            lang: Language code (default: ru)

        Returns:
            MP3 audio bytes
        """
        # Try Kokoro first
        if self.kokoro_api_key:
            try:
                return await self._synthesize_kokoro(text, lang)
            except Exception:
                pass  # Fall through to FreeTTS

        # Use FreeTTS as fallback
        return await self._synthesize_freetts(text, lang)

    async def _synthesize_kokoro(self, text: str, lang: str) -> bytes:
        """Synthesize using Kokoro API."""
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
            resp = await client.post(
                self.kokoro_url,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.content

    async def _synthesize_freetts(self, text: str, lang: str) -> bytes:
        """Synthesize using FreeTTS API (fallback)."""
        payload = {"text": text, "lang": lang}
        headers = {}
        if self.freetts_api_key:
            headers["Authorization"] = f"Bearer {self.freetts_api_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.freetts_url,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.content
