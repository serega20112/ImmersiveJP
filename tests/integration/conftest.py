"""Интеграционные фикстуры: сборка минимальных ASGI-приложений с middleware."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from src.infrastructures.observability import HttpMetricsCollector, get_logger
from src.presentation.http.middleware import (
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def static_directory() -> Path:
    """Директория статики фронтенда для монтирования в тестовых приложениях."""
    return PROJECT_ROOT / "src" / "frontend" / "static"


@pytest.fixture
def build_base_app() -> FastAPI:
    """Тестовое приложение с базовым стеком middleware (без лимитера и CSRF).

    Returns:
        FastAPI с Metrics/Logging/State/Session слоями и собранным
        HttpMetricsCollector в app.state.metrics_collector.
    """
    app = FastAPI()
    app.state.metrics_collector = HttpMetricsCollector()
    app.add_middleware(RequestMetricsMiddleware, collector=app.state.metrics_collector)
    app.add_middleware(RequestLoggingMiddleware, logger=get_logger("tests"))
    app.add_middleware(RequestStateMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test-secret")
    return app
