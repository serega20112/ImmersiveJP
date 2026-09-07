"""Роут страницы плана обучения."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_authenticated_user
from src.infrastructures.di_containers.service_dependencies import ProfileServiceDependency
from src.presentation.http import render_template

plan_page_router = APIRouter()


@plan_page_router.get("/plan", name="profile.plan_page")
async def plan_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу плана обучения.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь.
        profile_service: Сервис профиля.

    Returns:
        Ответ с шаблоном плана обучения.
    """
    page = await profile_service.build_learning_plan(current_user.id)
    return await render_template(request, "profile/plan.html", page=page)
