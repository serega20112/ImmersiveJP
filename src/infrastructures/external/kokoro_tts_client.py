from __future__ import annotations

import os

import httpx


class KokoroClient:
    """TTS client for Kokoro API.

    Provides text-to-speech synthesis with Russian language support.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("KOKORO_API_KEY", "")
        self.base_url = os.getenv("KOKORO_URL", "https://api.kokoro.ai/tts")
        self.voice = os.getenv("KOKORO_VOICE", "ru-RU-Dmitry")

    async def synthesize(self, text: str, lang: str = "ru") -> bytes:
        """Synthesize text to speech and return MP3 bytes.

        Args:
            text: Text to synthesize
            lang: Language code (default: ru)

        Returns:
            MP3 audio bytes
        """
        payload = {
            "text": text,
            "lang": lang,
            "voice": self.voice,
            "format": "mp3",
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.base_url,
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.content
