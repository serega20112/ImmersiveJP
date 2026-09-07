"""Роуты речевой практики."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import render_template
from src.presentation.http.schemas import SpeechPracticeForm

speech_router = APIRouter()


@speech_router.get("/speech", name="learning.speech_page")
async def speech_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу речевой практики.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.

    Returns:
        Ответ с шаблоном речевой практики.
    """
    page = await learning_service.get_speech_practice_page(current_user.id)
    return await render_template(request, "learn/speech.html", page=page)


@speech_router.post("/speech", name="learning.speech_generate")
async def speech_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    form: Annotated[SpeechPracticeForm, Depends()],
) -> HTMLResponse:
    """Обработать генерацию речевой практики.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.
        form: Данные формы генерации практики.

    Returns:
        Ответ с шаблоном практики.

    Ошибки генерации практики обрабатываются глобальными обработчиками.
    """
    page = await learning_service.generate_speech_practice(
        current_user.id,
        form.words_text,
    )
    return await render_template(request, "learn/speech.html", page=page)
