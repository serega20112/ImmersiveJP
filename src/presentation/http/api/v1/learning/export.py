"""Роуты генерации следующего батча и экспорта карточек."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.di_containers.auth_dependencies import require_authenticated_user
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import flash
from src.presentation.http.api.v1.learning.tracks import track_href
from src.presentation.http.schemas import TrackQuery

export_router = APIRouter()


@export_router.get("/next", name="learning.next_cards")
async def next_cards(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    query: Annotated[TrackQuery, Depends()],
) -> RedirectResponse:
    """Обработать генерацию следующего батча карточек.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        learning_service: Сервис обучения.
        query: Параметры трека обучения.

    Returns:
        Редирект на страницу трека.

    Ошибки генерации батча обрабатываются глобальными обработчиками.
    """
    await learning_service.get_next_cards(current_user.id, TrackType(query.track))
    flash(request, "Следующая партия готова.", "success")
    return RedirectResponse(
        url=track_href(query.track), status_code=status.HTTP_303_SEE_OTHER
    )


@export_router.get("/download-pdf", name="learning.download_pdf")
async def download_pdf(
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    query: Annotated[TrackQuery, Depends()],
) -> Response:
    """Обработать экспорт завершённых карточек в PDF.

    Args:
        current_user: Авторизованный пользователь.
        learning_service: Сервис обучения.
        query: Параметры трека обучения.

    Returns:
        Ответ с PDF-файлом.

    Ошибки экспорта обрабатываются глобальными обработчиками.
    """
    document = await learning_service.export_cards_to_pdf(
        current_user.id,
        TrackType(query.track),
    )
    headers = {"Content-Disposition": f'attachment; filename="{document.filename}"'}
    return Response(content=document.content, media_type=document.media_type, headers=headers)
