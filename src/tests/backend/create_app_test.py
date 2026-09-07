from __future__ import annotations

from src.presentation.http.web.middleware import (
    CsrfMiddleware,
    RateLimitMiddleware,
    RequestContainerMiddleware,
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)
from starlette.middleware.sessions import SessionMiddleware

from src.presentation.http.app import create_app


def test_middleware_order_matches_request_lifecycle():
    app = create_app()
    middleware_classes = [middleware.cls for middleware in app.user_middleware]

    assert middleware_classes == [
        SessionMiddleware,
        RequestStateMiddleware,
        RequestLoggingMiddleware,
        RequestMetricsMiddleware,
        RateLimitMiddleware,
        CsrfMiddleware,
        RequestContainerMiddleware,
    ]
