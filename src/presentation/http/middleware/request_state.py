"""Middleware инициализации состояния запроса."""

from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructures.di_containers.request_scope import _UNRESOLVED_CURRENT_USER


class RequestStateMiddleware(BaseHTTPMiddleware):
    """Заполняет базовое состояние запроса до обработки роутами."""

    async def dispatch(self, request: Request, call_next):
        """Инициализировать request_id, сессию БД и текущего пользователя.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя обработки.
        """
        request.state.request_id = uuid4().hex
        request.state.db_session = None
        request.state.current_user = _UNRESOLVED_CURRENT_USER
        return await call_next(request)
