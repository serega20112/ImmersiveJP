from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from src.backend.create_app import create_app
from src.backend.infrastructure.cache import KeyValueStore
from src.backend.infrastructure.observability import HttpMetricsCollector, get_logger
from src.backend.infrastructure.security import RateLimiter
from src.backend.infrastructure.web import register_exception_handlers
from src.backend.infrastructure.web.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)

PROJECT_ROOT = Path(__file__).resolve().parents[6]


def test_metrics_endpoint_renders_prometheus_snapshot():
    app = create_app()

    with TestClient(app) as client:
        client.get("/", follow_redirects=False)
        response = client.get("/metrics", follow_redirects=False)

    assert response.status_code == 200
    assert "immersjp_http_requests_total" in response.text
    assert 'route="/"' in response.text


def test_rate_limit_middleware_returns_429_and_headers():
    app = FastAPI()
    app.state.metrics_collector = HttpMetricsCollector()
    app.mount(
        "/static",
        StaticFiles(directory=str(PROJECT_ROOT / "src" / "frontend" / "static")),
        name="static",
    )
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=RateLimiter(KeyValueStore(redis_url=None, namespace="test-rate")),
        limit=1,
        window_seconds=60,
    )
    app.add_middleware(
        RequestMetricsMiddleware,
        collector=app.state.metrics_collector,
    )
    app.add_middleware(RequestLoggingMiddleware, logger=get_logger(__name__))
    app.add_middleware(RequestStateMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    register_exception_handlers(app)

    with TestClient(app) as client:
        first = client.get("/ping", follow_redirects=False)
        second = client.get("/ping", follow_redirects=False)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"] == "60"
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"
