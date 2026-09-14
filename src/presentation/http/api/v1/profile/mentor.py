"""Роуты страницы ментора в профиле."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_authenticated_user
from src.infrastructures.di_containers.service_dependencies import ProfileServiceDependency
from src.presentation.http import render_template
from src.presentation.http.schemas import MentorMessageForm

profile_mentor_router = APIRouter()


@profile_mentor_router.get("/mentor", name="profile.mentor_page")
async def mentor_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу ментора.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        profile_service: Сервис профиля.

    Returns:
        Ответ с шаблоном ментора.
    """
    page = await profile_service.get_mentor_page(current_user.id)
    return await render_template(request, "profile/mentor.html", page=page)


@profile_mentor_router.post("/mentor", name="profile.mentor_send")
async def mentor_send(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
    form: Annotated[MentorMessageForm, Form()],
) -> HTMLResponse:
    """Обработать отправку сообщения ментору.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        profile_service: Сервис профиля.
        form: Данные формы сообщения.

    Returns:
        Ответ с шаблоном ментора и ответом ментора.

    Ошибки некорректного сообщения обрабатываются глобальными обработчиками.
    """
    page = await profile_service.send_mentor_message(current_user.id, form.message)
    return await render_template(request, "profile/mentor.html", page=page)
