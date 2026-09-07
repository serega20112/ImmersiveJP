"""Роут страницы профиля."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_authenticated_user
from src.infrastructures.di_containers.service_dependencies import ProfileServiceDependency
from src.presentation.http import render_template

profile_page_router = APIRouter()


@profile_page_router.get("/profile", name="profile.page")
async def profile_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу профиля с прогрессом и советом.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        profile_service: Сервис профиля.

    Returns:
        Ответ с шаблоном профиля.
    """
    report = await profile_service.build_progress_report(current_user.id)
    advice = await profile_service.generate_ai_advice(current_user.id, report)
    return await render_template(request, "profile/index.html", report=report, advice=advice)
