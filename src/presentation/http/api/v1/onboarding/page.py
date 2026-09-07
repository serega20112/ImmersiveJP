"""Роут страницы онбординга."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_registered_user
from src.infrastructures.di_containers.service_dependencies import OnboardingServiceDependency
from src.presentation.http import RouteRedirectError, render_template

onboarding_page_router = APIRouter()


@onboarding_page_router.get("/onboarding", name="onboarding.page")
async def onboarding_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_registered_user)],
    onboarding_service: OnboardingServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу онбординга.

    Args:
        request: Входящий запрос.
        current_user: Зарегистрированный пользователь.
        onboarding_service: Сервис онбординга.

    Returns:
        Ответ с шаблоном онбординга.

    Если онбординг уже завершён, выполняется редирект на дашборд
    через ``RouteRedirectError``.
    """
    if current_user.onboarding_completed:
        raise RouteRedirectError(request.app.url_path_for("dashboard.dashboard_page"))
    page = await onboarding_service.get_page()
    return await render_template(request, "onboarding/index.html", page=page)
