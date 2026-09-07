"""Роут страницы ментора."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import ProfileServiceDependency
from src.presentation.http import render_template

mentor_page_router = APIRouter()


@mentor_page_router.get("/", name="mentor.page")
async def tutor_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    profile_service: ProfileServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу ментора.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        profile_service: Сервис профиля.

    Returns:
        Ответ с шаблоном ментора.
    """
    page = await profile_service.get_mentor_page(current_user.id)
    return await render_template(request, "profile/mentor.html", page=page)
