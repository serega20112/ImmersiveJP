"""Middleware ограничения частоты запросов."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.exceptions import RateLimitExceededError
from src.infrastructures.security import RateLimiter
from src.presentation.http.exception_handlers import (
    application_error_response,
    apply_default_response_headers,
)
from src.presentation.http.middleware._helpers import is_static_request


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ограничивает частоту запросов по IP клиента."""

    def __init__(
        self,
        app,
        *,
        rate_limiter: RateLimiter,
        limit: int,
        window_seconds: int,
    ):
        """Инициализировать middleware.

        Args:
            app: Приложение ASGI.
            rate_limiter: Клиент ограничения частоты запросов.
            limit: Максимальное количество запросов за окно.
            window_seconds: Размер окна в секундах.
        """
        super().__init__(app)
        self._rate_limiter = rate_limiter
        self._limit = limit
        self._window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        """Учесть запрос в лимите и отклонить при превышении.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя либо ответ 429 с заголовками лимита.
        """
        if is_static_request(request) or request.url.path in {"/health", "/metrics"}:
            return await call_next(request)

        forwarded_for = str(request.headers.get("x-forwarded-for") or "").strip()
        client_host = forwarded_for.split(",")[0].strip() if forwarded_for else ""
        if not client_host:
            client_host = request.client.host if request.client is not None else "unknown"

        current_count = await self._rate_limiter.consume(
            scope="http-api",
            key=client_host,
            window_seconds=self._window_seconds,
        )
        remaining = max(self._limit - current_count, 0)
        if current_count > self._limit:
            return await application_error_response(
                request,
                RateLimitExceededError(
                    limit=self._limit,
                    remaining=remaining,
                    retry_after_seconds=self._window_seconds,
                ),
            )

        response = await call_next(request)
        apply_default_response_headers(request, response)
        response.headers.setdefault("X-RateLimit-Limit", str(self._limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        response.headers.setdefault("X-RateLimit-Window", str(self._window_seconds))
        return response
