"""Сборка FastAPI-приложения: middleware, шаблонизатор, роуты."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.config.settings import settings
from src.infrastructures.database import get_session_factory
from src.infrastructures.di_containers.container import container
from src.infrastructures.observability import HttpMetricsCollector, get_logger
from src.presentation.http import register_exception_handlers
from src.presentation.http.api import api_router
from src.presentation.http.middleware import (
    CsrfMiddleware,
    RateLimitMiddleware,
    RequestContainerMiddleware,
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield
    root_container = getattr(app.state, "root_container", None)
    if root_container is not None:
        await root_container.shutdown()


def create_app() -> FastAPI:
    """Собрать и настроить FastAPI-приложение.

    Returns:
        Полностью сконфигурированное приложение.
    """
    app = FastAPI(
        title=settings.app.app_name,
        debug=settings.app.app_debug,
        lifespan=_lifespan,
    )
    templates = Jinja2Templates(directory=str(FRONTEND_ROOT / "templates"))
    app.state.templates = templates
    app.state.root_container = container
    app.state.asset_version = str(int(time.time()))
    app.state.metrics_collector = HttpMetricsCollector()
    app.mount("/static", StaticFiles(directory=str(FRONTEND_ROOT / "static")), name="static")
    app.add_middleware(
        RequestContainerMiddleware,
        root_container=container,
        session_factory=get_session_factory(),
    )
    app.add_middleware(CsrfMiddleware)
    if settings.app.api_rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=container.rate_limiter,
            limit=settings.app.api_rate_limit_requests,
            window_seconds=settings.app.api_rate_limit_window_seconds,
        )
    app.add_middleware(
        RequestMetricsMiddleware,
        collector=app.state.metrics_collector,
    )
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
    app.add_middleware(RequestStateMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.security.session_secret,
        same_site=settings.security.cookie_samesite,
        https_only=settings.security.cookie_secure,
        session_cookie=settings.security.session_cookie_name,
    )
    app.include_router(api_router)
    register_exception_handlers(app)
    return app
