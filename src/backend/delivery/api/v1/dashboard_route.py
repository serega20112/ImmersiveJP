from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request

from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.service_dependencies import DashboardServiceDependency
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import render_template

dashboard_router = APIRouter()


@dashboard_router.get("/dashboard", name="dashboard.dashboard_page")
async def dashboard_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    dashboard_service: DashboardServiceDependency,
):
    dashboard = await dashboard_service.get_dashboard(current_user.id)
    return await render_template(request, "dashboard/index.html", dashboard=dashboard)
