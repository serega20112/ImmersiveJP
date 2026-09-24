"""Роуты карточек обучения."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.di_containers.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
)
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import flash, render_template
from src.presentation.http.api.v1.learning.tracks import resolve_return_to, track_href
from src.presentation.http.schemas import CompleteCardForm, GenerateBatchForm

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
        TrackType(track),
        card_id,
    )
    return await render_template(request, "learn/card.html", page=page)


@cards_router.post("/next", name="learning.next_cards")
async def next_cards(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    learning_service: LearningServiceDependency,
    form: Annotated[GenerateBatchForm, Form()],
) -> RedirectResponse:
    """Забронировать партию карточек и уйти генерировать в фон.

    Ответ уходит сразу: обращение к модели занимает десятки секунд, и ждать его
    в запросе означало бы держать страницу мёртвой. Страница трека сама
    опрашивает состояние партии и дорисовывает готовые карточки.

    Args:
        request: Входящий запрос.
        background_tasks: Фоновые задачи FastAPI, запускаемые после ответа.
        current_user: Авторизованный пользователь.
        learning_service: Сервис обучения.
        form: Данные формы с ключом трека.

    Returns:
        Редирект на страницу трека.

    Ошибки брони обрабатываются глобальными обработчиками.
    """
    track = TrackType(form.track)
    batch_number = await learning_service.start_batch_generation(current_user.id, track)
    background_tasks.add_task(learning_service.generate_batch, current_user.id, track, batch_number)
    flash(request, "Партия готовится, карточки появятся на странице.", "success")
    return RedirectResponse(url=track_href(form.track), status_code=status.HTTP_303_SEE_OTHER)


@cards_router.get("/{track}/batch-status", name="learning.batch_status")
async def batch_status(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: str,
) -> HTMLResponse:
    """Отдать HTML-фрагмент текущего состояния партии.

    Фрагмент вместо JSON: разметка карточки живёт в шаблонах, и второй её копии
    в JavaScript не должно появляться.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.
        track: Ключ трека обучения.

    Returns:
        Ответ с фрагментом списка карточек.

    Ошибки поиска трека обрабатываются глобальными обработчиками.
    """
    status_page = await learning_service.get_batch_status(current_user.id, TrackType(track))
    return await render_template(
        request,
        "learn/partials/batch_cards.html",
        status=status_page,
        track=track,
    )


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
