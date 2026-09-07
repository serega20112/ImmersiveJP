"""Роут выдачи Prometheus-метрик."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from src.application.exceptions import ApplicationError, ErrorCode
from src.config.settings import settings

metrics_router = APIRouter()


@metrics_router.get("/metrics", include_in_schema=False, name="system.metrics")
async def metrics_page(request: Request) -> PlainTextResponse:
    """Вернуть метрики в формате Prometheus.

    Args:
        request: Входящий запрос.

    Returns:
        Ответ с текстом метрик.

    Raises:
        ApplicationError: Если метрики отключены или коллектор недоступен.
    """
    if not settings.app.metrics_enabled:
        raise ApplicationError(
            code=ErrorCode.NOT_FOUND,
            message="Сбор метрик отключён в текущей конфигурации.",
        )
    collector = getattr(request.app.state, "metrics_collector", None)
    if collector is None:
        raise ApplicationError(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Коллектор метрик не инициализирован.",
        )
    return PlainTextResponse(
        collector.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
