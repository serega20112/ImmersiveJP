"""Роуты домашних работ по трекам."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import LearningServiceDependency
from src.presentation.http import render_template

work_router = APIRouter()


@work_router.get("/{track}/work/{batch_number}", name="learning.work_page")
async def work_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: str,
    batch_number: int,
) -> HTMLResponse:
    """Отрисовать страницу домашней работы по батчу.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.
        track: Ключ трека обучения.
        batch_number: Номер батча.

    Returns:
        Ответ с шаблоном работы.

        Ошибки доступности работы обрабатываются глобальными обработчиками.
    """
    page = await learning_service.get_track_work_page(
        current_user.id,
        track,
        batch_number,
    )
    return await render_template(request, "learn/work.html", page=page)


@work_router.post("/{track}/work/{batch_number}", name="learning.work_submit")
async def work_submit(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    learning_service: LearningServiceDependency,
    track: str,
    batch_number: int,
) -> HTMLResponse:
    """Обработать отправку ответов домашней работы.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        learning_service: Сервис обучения.
        track: Ключ трека обучения.
        batch_number: Номер батча.

    Returns:
        Ответ с результатами проверки.

        Ошибки проверки работы обрабатываются глобальными обработчиками.
    """
    form = await request.form()
    answers = {
        key.removeprefix("answer_"): str(value)
        for key, value in form.items()
        if key.startswith("answer_")
    }
    page = await learning_service.submit_track_work(
        current_user.id,
        track,
        batch_number,
        answers,
    )
    return await render_template(request, "learn/work.html", page=page)
