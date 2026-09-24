"""
Интеграционные тесты стека middleware create_app.

Проверяется порядок middleware в ASGI-стеке: он должен соответствовать
обратному порядку регистрации и реальному жизненному циклу запроса.
"""

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from src.config.settings import settings
from src.presentation.http.app import create_app
from src.presentation.http.middleware import (
    CsrfMiddleware,
    RateLimitMiddleware,
    RequestContainerMiddleware,
    RequestLoggingMiddleware,
    RequestMetricsMiddleware,
    RequestStateMiddleware,
)


class TestMiddlewareStack:
    """Группа тестов порядка middleware собранного приложения."""

    def test_middleware_order_matches_request_lifecycle(self) -> None:
        """
        Тестируем: порядок middleware, зарегистрированных create_app.
        Отдаём: приложение без внешних зависимостей (без запуска сервера).
        Ожидаем: стек от внешнего слоя к внутреннему — Session, RequestState,
                 RequestLogging, RequestMetrics, [RateLimit], Csrf, RequestContainer;
                 RateLimit присутствует, если включён в настройках.
        """
        app: FastAPI = create_app()
        middleware_classes = [middleware.cls for middleware in app.user_middleware]

        expected: list[type] = [
            SessionMiddleware,
            RequestStateMiddleware,
            RequestLoggingMiddleware,
            RequestMetricsMiddleware,
        ]
        if settings.app.api_rate_limit_enabled:
            expected.append(RateLimitMiddleware)
        expected.extend([CsrfMiddleware, RequestContainerMiddleware])

        assert middleware_classes == expected
