"""Middleware запросного scope DI-контейнера."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructures.di_containers.container import Container
from src.infrastructures.di_containers.request_scope import (
    bind_request_container,
    release_request_container,
)


class RequestContainerMiddleware(BaseHTTPMiddleware):
    """Создаёт запросный scope контейнера и освобождает его после ответа."""

    def __init__(
        self,
        app,
        *,
        root_container: Container,
        session_factory: Callable[[], AsyncSession],
    ):
        """Инициализировать middleware.

        Args:
            app: Приложение ASGI.
            root_container: Корневой DI-контейнер.
            session_factory: Фабрика сессий БД.
        """
        super().__init__(app)
        self._root_container = root_container
        self._session_factory = session_factory

    async def dispatch(self, request: Request, call_next):
        """Выполнить запрос внутри запросного scope контейнера.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя обработки.
        """
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
