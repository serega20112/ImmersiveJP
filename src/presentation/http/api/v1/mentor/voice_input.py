"""Роут распознавания голосового ввода."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import STTClientDependency
from src.presentation.http.schemas import VoiceInputResponse

mentor_voice_router = APIRouter()


@mentor_voice_router.post(
    "/voice-input",
    name="mentor.voice_input",
    response_model=VoiceInputResponse,
)
async def tutor_voice_input(
    _request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    stt_client: STTClientDependency,
    audio: UploadFile = File(),  # noqa: B008
) -> VoiceInputResponse:
    """Обработать голосовой ввод и распознать речь.

    Args:
        _request: Входящий запрос.
        _current_user: Авторизованный пользователь с онбордингом.
        stt_client: Клиент распознавания речи.
        audio: Загруженный аудиофайл.

    Returns:
        Схема с распознанным текстом.
    """
    audio_data = await audio.read()
    text = await stt_client.transcribe(audio_data)
    return VoiceInputResponse(text=text)
