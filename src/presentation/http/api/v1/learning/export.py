"""Роут экспорта карточек."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from src.application.dto.auth import UserViewDTO
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.di_containers.auth_dependencies import require_authenticated_user
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http.schemas import TrackQuery

export_router = APIRouter()


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
