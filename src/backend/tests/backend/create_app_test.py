from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.backend.create_app import create_app


def test_session_middleware_wraps_request_scope_middleware():
    app = create_app()
    middleware_classes = [middleware.cls for middleware in app.user_middleware]

    assert middleware_classes.index(SessionMiddleware) < middleware_classes.index(
        BaseHTTPMiddleware
    )
