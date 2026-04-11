from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.web.errors import ApplicationError

system_router = APIRouter()


@system_router.get("/health", include_in_schema=False, name="system.health")
async def health_page():
    return JSONResponse(
        {
            "status": "ok",
            "app": Settings.app_name,
            "metrics_enabled": Settings.metrics_enabled,
            "rate_limit_enabled": Settings.api_rate_limit_enabled,
        }
    )


@system_router.get("/metrics", include_in_schema=False, name="system.metrics")
async def metrics_page(request: Request):
    if not Settings.metrics_enabled:
        raise ApplicationError(
            status_code=404,
            title="Метрики отключены",
            message="Сбор метрик отключен в текущей конфигурации.",
        )
    collector = getattr(request.app.state, "metrics_collector", None)
    if collector is None:
        raise ApplicationError(
            status_code=503,
            title="Метрики недоступны",
            message="Коллектор метрик не инициализирован.",
        )
    return PlainTextResponse(
        collector.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
