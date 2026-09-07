"""Роут проверки работоспособности приложения."""

from __future__ import annotations

from fastapi import APIRouter

from src.config.settings import settings
from src.presentation.http.schemas import SystemHealthResponse

health_router = APIRouter()


@health_router.get(
    "/health",
    include_in_schema=False,
    name="system.health",
    response_model=SystemHealthResponse,
)
async def health_page() -> SystemHealthResponse:
    """Вернуть статус работоспособности приложения.

    Returns:
        Схема статуса системы.
    """
    return SystemHealthResponse(
        status="ok",
        app=settings.app.app_name,
        metrics_enabled=settings.app.metrics_enabled,
        rate_limit_enabled=settings.app.api_rate_limit_enabled,
    )
