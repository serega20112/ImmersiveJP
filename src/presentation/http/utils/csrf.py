"""Проверка CSRF-токенов для защищённых методов запросов."""

from __future__ import annotations

from secrets import compare_digest, token_urlsafe

from fastapi import Request

from src.application.exceptions import SecurityViolationError
from src.config.settings import settings

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def ensure_csrf_token(request: Request) -> str:
    """Получить токен из сессии или выпустить новый.

    Args:
        request: Входящий запрос.

    Returns:
        Действующий CSRF-токен сессии.
    """
    csrf_session_key = settings.security.csrf_session_key
    token = str(request.session.get(csrf_session_key) or "").strip()
    if token:
        return token
    token = token_urlsafe(32)
    request.session[csrf_session_key] = token
    return token


async def validate_csrf(request: Request) -> None:
    """Проверить CSRF-токен для незащищённых методов.

    Args:
        request: Входящий запрос.

    Raises:
        SecurityViolationError: Токен отсутствует или не совпадает.
    """
    if request.method.upper() in _SAFE_METHODS:
        ensure_csrf_token(request)
        return

    session_token = ensure_csrf_token(request)
    csrf_header_name = settings.security.csrf_header_name
    csrf_field_name = settings.security.csrf_field_name
    submitted_token = str(request.headers.get(csrf_header_name) or "").strip()
    if not submitted_token:
        content_type = str(request.headers.get("content-type") or "").lower()
        if (
            "application/x-www-form-urlencoded" in content_type
            or "multipart/form-data" in content_type
        ):
            await request.body()
            form = await request.form()
            submitted_token = str(form.get(csrf_field_name) or "").strip()

    if not submitted_token or not compare_digest(session_token, submitted_token):
        raise SecurityViolationError()
