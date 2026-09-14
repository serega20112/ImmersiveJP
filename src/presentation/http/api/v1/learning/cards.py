"""Роуты карточек обучения."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
)
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import flash, render_template
from src.presentation.http.api.v1.learning.tracks import resolve_return_to, track_href
from src.presentation.http.schemas import CompleteCardForm

cards_router = APIRouter()


@cards_router.get("/{track}/cards/{card_id}", name="learning.card_page")
async def card_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: str,
    card_id: int,
) -> HTMLResponse:
    """Отрисовать страницу карточки.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.
        track: Ключ трека обучения.
        card_id: Идентификатор карточки.

    Returns:
        Ответ с шаблоном карточки.

    Ошибки поиска карточки обрабатываются глобальными обработчиками.
    """
    page = await learning_service.get_card_page(
        current_user.id,
        track,
        card_id,
    )
    return await render_template(request, "learn/card.html", page=page)


@cards_router.post("/complete", name="learning.complete_card")
async def complete_card(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    form: Annotated[CompleteCardForm, Form()],
) -> RedirectResponse:
    """Обработать отметку карточки как пройденной.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        learning_service: Сервис обучения.
        form: Данные формы завершения карточки.

    Returns:
        Редирект на адрес возврата.

    Ошибки владения карточкой обрабатываются глобальными обработчиками.
    """
    await learning_service.complete_card(current_user.id, form.card_id)
    flash(request, "Карточка отмечена как пройденная.", "success")
    return RedirectResponse(
        url=resolve_return_to(form.return_to, track_href(form.track)),
        status_code=status.HTTP_303_SEE_OTHER,
    )
