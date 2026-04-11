from __future__ import annotations

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from src.backend.dependencies.container import Container
from src.backend.dependencies.request_scope import (
    _UNRESOLVED_CURRENT_USER,
    bind_request_container,
    release_request_container,
)
from src.backend.infrastructure.observability import HttpMetricsCollector, log_event
from src.backend.infrastructure.security import RateLimiter
from src.backend.infrastructure.web.csrf import validate_csrf
from src.backend.infrastructure.web.error_responses import (
    apply_default_response_headers,
    build_application_error_response,
)
from src.backend.infrastructure.web.errors import ApplicationError, RateLimitExceededError


def _is_static_request(request: Request) -> bool:
    return request.url.path.startswith("/static") or request.url.path == "/favicon.ico"


def _resolve_route_label(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return str(route_path)
    return request.url.path or "/"


def _resolve_user_id(request: Request) -> int | None:
    current_user = getattr(request.state, "current_user", None)
    return getattr(current_user, "id", None)


class RequestStateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = uuid4().hex
        request.state.db_session = None
        request.state.current_user = _UNRESOLVED_CURRENT_USER
        return await call_next(request)


class RequestContainerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        root_container: Container,
        session_factory: Callable[[], AsyncSession],
    ):
        super().__init__(app)
        self._root_container = root_container
        self._session_factory = session_factory

    async def dispatch(self, request: Request, call_next):
        request_container = self._root_container.scope(
            session_factory=self._session_factory,
            request_state=request.state,
        )
        context_token = bind_request_container(request_container)
        try:
            return await call_next(request)
        finally:
            release_request_container(context_token)
            await request_container.aclose()


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            await validate_csrf(request)
        except ApplicationError as error:
            return await build_application_error_response(request, error)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        rate_limiter: RateLimiter,
        limit: int,
        window_seconds: int,
    ):
        super().__init__(app)
        self._rate_limiter = rate_limiter
        self._limit = limit
        self._window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        if _is_static_request(request) or request.url.path in {"/health", "/metrics"}:
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
            return await build_application_error_response(
                request,
                RateLimitExceededError(
                    limit=self._limit,
                    remaining=remaining,
                    retry_after_seconds=self._window_seconds,
                ),
            )

        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Limit", str(self._limit))
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        response.headers.setdefault("X-RateLimit-Window", str(self._window_seconds))
        return response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, collector: HttpMetricsCollector):
        super().__init__(app)
        self._collector = collector

    async def dispatch(self, request: Request, call_next):
        if _is_static_request(request):
            return await call_next(request)

        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except ApplicationError as error:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            route_label = _resolve_route_label(request)
            self._collector.record_request(
                method=request.method,
                route=route_label,
                status_code=error.status_code,
                duration_ms=duration_ms,
            )
            if isinstance(error, RateLimitExceededError):
                self._collector.record_rate_limited(route=route_label)
            raise
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            route_label = _resolve_route_label(request)
            self._collector.record_request(
                method=request.method,
                route=route_label,
                status_code=500,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        route_label = _resolve_route_label(request)
        self._collector.record_request(
            method=request.method,
            route=route_label,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, logger):
        super().__init__(app)
        self._logger = logger

    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
        except ApplicationError as error:
            if not _is_static_request(request):
                log_event(
                    self._logger,
                    logging.WARNING,
                    error.event,
                    error.message,
                    request_id=getattr(request.state, "request_id", None),
                    path=request.url.path,
                    method=request.method,
                    user_id=_resolve_user_id(request),
                    status_code=error.status_code,
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
            raise
        except Exception:
            if not _is_static_request(request):
                log_event(
                    self._logger,
                    logging.ERROR,
                    "http.request_failed",
                    "Request failed",
                    request_id=getattr(request.state, "request_id", None),
                    path=request.url.path,
                    method=request.method,
                    user_id=_resolve_user_id(request),
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
            raise

        if not _is_static_request(request):
            log_event(
                self._logger,
                logging.INFO,
                "http.request_completed",
                "Request completed",
                request_id=getattr(request.state, "request_id", None),
                path=request.url.path,
                method=request.method,
                user_id=_resolve_user_id(request),
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )

        apply_default_response_headers(request, response)
        return response
