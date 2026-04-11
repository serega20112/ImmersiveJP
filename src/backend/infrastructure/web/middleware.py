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
from src.backend.infrastructure.observability import log_event
from src.backend.infrastructure.web.csrf import validate_csrf


def _is_static_request(request: Request) -> bool:
    return request.url.path.startswith("/static") or request.url.path == "/favicon.ico"


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
        await validate_csrf(request)
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, logger):
        super().__init__(app)
        self._logger = logger

    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
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
                    user_id=getattr(
                        getattr(request.state, "current_user", None), "id", None
                    ),
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
                user_id=getattr(
                    getattr(request.state, "current_user", None), "id", None
                ),
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )

        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers.setdefault("X-Request-ID", request_id)
        return response
