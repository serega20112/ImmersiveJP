"""Роуты страниц треков обучения."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.application.services import LearningService
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import render_template

tracks_router = APIRouter()

TRACK_HREFS = {
    "language": "/learn/language",
    "culture": "/learn/culture",
    "history": "/learn/history",
}


def track_href(track: str) -> str:
    """Получить адрес страницы трека по ключу.

    Args:
        track: Ключ трека (language, culture, history).

    Returns:
        URL-путь страницы трека.
    """
    return TRACK_HREFS[track]


def resolve_return_to(return_to: str | None, fallback: str) -> str:
    """Определить безопасный адрес возврата.

    Args:
        return_to: Адрес возврата из формы.
        fallback: Адрес по умолчанию.

    Returns:
        Валидный относительный адрес возврата.
    """
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return fallback


async def render_track_page(
    request: Request,
    current_user: UserViewDTO,
    track: TrackType,
    learning_service: LearningService,
) -> HTMLResponse:
    """Отрисовать страницу трека.

    Args:
        request: Входящий запрос.
        current_user: Текущий пользователь.
        track: Тип трека обучения.
        learning_service: Сервис обучения.

    Returns:
        Ответ с шаблоном трека.
    """
    page = await learning_service.get_track_page(current_user.id, track)
    status = await learning_service.get_batch_status(current_user.id, track)
    return await render_template(
        request,
        "learn/track.html",
        page=page,
        status=status,
        track=page.track,
    )


@tracks_router.get("/language", name="learning.language")
async def language_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу трека языка.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.

    Returns:
        Ответ с шаблоном трека.
    """
    return await render_track_page(request, current_user, TrackType.LANGUAGE, learning_service)


@tracks_router.get("/culture", name="learning.culture")
async def culture_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу трека культуры.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.

    Returns:
        Ответ с шаблоном трека.
    """
    return await render_track_page(request, current_user, TrackType.CULTURE, learning_service)


@tracks_router.get("/history", name="learning.history")
async def history_track(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу трека истории.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.

    Returns:
        Ответ с шаблоном трека.
    """
    return await render_track_page(request, current_user, TrackType.HISTORY, learning_service)
