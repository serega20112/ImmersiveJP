"""
Интеграционные тесты RateLimitMiddleware.

Проверяются: пропуск запросов в пределах лимита, отклонение 429
с заголовками Retry-After и X-RateLimit-* при превышении, а также
исключение статики и служебных путей из лимита.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from src.infrastructures.cache import KeyValueStore
from src.infrastructures.observability import HttpMetricsCollector, get_logger
from src.infrastructures.security import RateLimiter
from src.presentation.http import register_exception_handlers
from src.presentation.http.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)


def _build_limited_app(static_directory: Path) -> FastAPI:
    """Собрать приложение с лимитом 1 запрос на окно 60 секунд.

    Args:
        static_directory: Директория статики для монтирования /static.

    Returns:
        Приложение с полным базовым стеком middleware и лимитером.
    """
    app = FastAPI()
    app.state.metrics_collector = HttpMetricsCollector()
    app.state.templates = Jinja2Templates(directory=str(static_directory.parent / "templates"))
    app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=RateLimiter(KeyValueStore(redis_url=None, namespace="test-rate")),
        limit=1,
        window_seconds=60,
    )
    app.add_middleware(RequestMetricsMiddleware, collector=app.state.metrics_collector)
    app.add_middleware(RequestLoggingMiddleware, logger=get_logger("tests"))
    app.add_middleware(RequestStateMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.get("/ping")
    async def ping():
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        return {"status": "metrics"}

    register_exception_handlers(app)
    return app


class TestRateLimitMiddleware:
    """Группа тестов ограничения частоты запросов."""

    def test_returns_429_and_headers_on_exceeded_limit(self, static_directory: Path) -> None:
        """
        Тестируем: поведение при превышении лимита запросов.
        Отдаём: лимит 1 запрос за 60 секунд; два подряд GET /ping.
        Ожидаем: первый запрос 200, второй — 429 с заголовками Retry-After=60,
                 X-RateLimit-Limit=1, X-RateLimit-Remaining=0.
        """
        app = _build_limited_app(static_directory)

        with TestClient(app) as client:
            first = client.get("/ping", follow_redirects=False)
            second = client.get("/ping", follow_redirects=False)

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert second.headers["Retry-After"] == "60"
        assert second.headers["X-RateLimit-Limit"] == "1"
        assert second.headers["X-RateLimit-Remaining"] == "0"

    def test_static_and_service_paths_bypass_limit(self, static_directory: Path) -> None:
        """
        Тестируем: исключения из лимита для статики и служебных путей.
        Отдаём: лимит 1 запрос; несколько запросов к /metrics и статике
                (маршрут /metrics объявлен заглушкой в тестовом приложении).
        Ожидаем: ни один запрос не получает 429.
        """
        app = _build_limited_app(static_directory)

        with TestClient(app) as client:
            first = client.get("/metrics", follow_redirects=False)
            second = client.get("/metrics", follow_redirects=False)
            static_file = client.get("/static/css/main.css", follow_redirects=False)

        assert first.status_code == status.HTTP_200_OK
        assert second.status_code == status.HTTP_200_OK
        assert static_file.status_code == status.HTTP_200_OK
