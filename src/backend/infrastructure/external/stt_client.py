from __future__ import annotations

import logging

import httpx

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.observability import get_logger, log_event

logger = get_logger(__name__)


class STTClient:
    _WHISPER_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

    def __init__(self) -> None:
        self._http_client = httpx.AsyncClient(timeout=30)

    async def transcribe(self, audio_data: bytes) -> str:
        if not Settings.hf_api_token:
            log_event(logger, logging.WARNING, "stt.missing_token", "HF API token not configured")
            return ""
        try:
            resp = await self._http_client.post(
                self._WHISPER_URL,
                content=audio_data,
                headers={
                    "Authorization": f"Bearer {Settings.hf_api_token}",
                    "Content-Type": "audio/webm",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            text = str(result.get("text", "")).strip()
            log_event(
                logger,
                logging.INFO,
                "stt.transcribed",
                "Audio transcribed successfully",
                length=len(text),
            )
            return text
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "stt.transcribe_error",
                "STT transcription failed",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            return ""

    async def close(self) -> None:
        await self._http_client.aclose()
