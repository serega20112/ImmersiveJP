"""Middleware проверки CSRF-токенов."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.exceptions import ApplicationError
from src.presentation.http.exception_handlers import application_error_response
from src.presentation.http.utils.csrf import validate_csrf


class CsrfMiddleware(BaseHTTPMiddleware):
    """Отклоняет запросы с некорректным CSRF-токеном."""

    async def dispatch(self, request: Request, call_next):
        """Проверить CSRF-токен и вернуть ответ об ошибке при нарушении.

        Args:
            request: Входящий запрос.
            call_next: Обработчик следующего слоя.

        Returns:
            Ответ следующего слоя либо ответ с ошибкой безопасности.
        """
        try:
            await validate_csrf(request)
        except ApplicationError as error:
            return await application_error_response(request, error)
        return await call_next(request)
