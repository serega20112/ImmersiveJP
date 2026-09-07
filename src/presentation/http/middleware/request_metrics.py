"""Middleware сбора HTTP-метрик."""

from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.exceptions import ApplicationError, RateLimitExceededError
from src.infrastructures.observability import HttpMetricsCollector
from src.presentation.http.exception_handlers import error_status_code
from src.presentation.http.middleware._helpers import (
    is_static_request,
    resolve_route_label,
)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Фиксирует длительность и статус каждого запроса в метриках."""

    def __init__(self, app, *, collector: HttpMetricsCollector):
        """Инициализировать middleware.

        Args:
            app: Приложение ASGI.
            collector: Коллектор HTTP-метрик.
        """
        super().__init__(app)
        self._collector = collector

    async def dispatch(self, request: Request, call_next):
        """Записать метрики запроса, включая ошибки приложения.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя обработки.
        """
        if is_static_request(request):
            return await call_next(request)

        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except ApplicationError as error:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            route_label = resolve_route_label(request)
            self._collector.record_request(
                method=request.method,
                route=route_label,
                status_code=error_status_code(error),
                duration_ms=duration_ms,
            )
            if isinstance(error, RateLimitExceededError):
                self._collector.record_rate_limited(route=route_label)
            raise
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            route_label = resolve_route_label(request)
            self._collector.record_request(
                method=request.method,
                route=route_label,
                status_code=500,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route_label = resolve_route_label(request)
        self._collector.record_request(
            method=request.method,
            route=route_label,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
