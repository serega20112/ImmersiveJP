"""Middleware журналирования HTTP-запросов."""

from __future__ import annotations

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.exceptions import ApplicationError
from src.infrastructures.observability import log_event
from src.presentation.http.exception_handlers import (
    apply_default_response_headers,
    error_status_code,
)
from src.presentation.http.middleware._helpers import is_static_request, resolve_user_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Пишет структурный журнал запросов и применяет заголовки безопасности."""

    def __init__(self, app, *, logger):
        """Инициализировать middleware.

        Args:
            app: Приложение ASGI.
            logger: Логгер для записи событий.
        """
        super().__init__(app)
        self._logger = logger

    async def dispatch(self, request: Request, call_next):
        """Записать событие обработки запроса и добавить заголовки.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя обработки.
        """
        started_at = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
        except ApplicationError as error:
            if not is_static_request(request):
                log_event(
                    self._logger,
                    logging.WARNING,
                    f"http.{error.code.value.lower()}",
                    error.message,
                    request_id=getattr(request.state, "request_id", None),
                    path=request.url.path,
                    method=request.method,
                    user_id=resolve_user_id(request),
                    status_code=error_status_code(error),
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
            raise
        except Exception:
            if not is_static_request(request):
                log_event(
                    self._logger,
                    logging.ERROR,
                    "http.request_failed",
                    "Request failed",
                    request_id=getattr(request.state, "request_id", None),
                    path=request.url.path,
                    method=request.method,
                    user_id=resolve_user_id(request),
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
            raise

        if not is_static_request(request):
            log_event(
                self._logger,
                logging.INFO,
                "http.request_completed",
                "Request completed",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                user_id=resolve_user_id(request),
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )

        apply_default_response_headers(request, response)
        return response
