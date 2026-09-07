"""Роут страницы дашборда."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import DashboardServiceDependency
from src.presentation.http import render_template

dashboard_page_router = APIRouter()


@dashboard_page_router.get("/dashboard", name="dashboard.dashboard_page")
async def dashboard_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    dashboard_service: DashboardServiceDependency,
) -> HTMLResponse:
    """Отрисовать страницу дашборда.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        dashboard_service: Сервис дашборда.

    Returns:
        Ответ с шаблоном дашборда.
    """
    dashboard = await dashboard_service.get_dashboard(current_user.id)
    return await render_template(request, "dashboard/index.html", dashboard=dashboard)
