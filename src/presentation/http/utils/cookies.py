"""Установка и очистка аутентификационных cookie."""

from __future__ import annotations

from fastapi.responses import RedirectResponse

from src.config.settings import settings


def set_auth_cookies(
    response: RedirectResponse,
    access_token: str,
    refresh_token: str,
) -> None:
    """Установить access- и refresh-cookie на ответ.

    Args:
        response: Ответ, в который добавляются cookie.
        access_token: Access-токен.
        refresh_token: Refresh-токен.
    """
    cookie_kwargs = {
        "httponly": True,
        "samesite": settings.security.cookie_samesite,
        "secure": settings.security.cookie_secure,
        "path": "/",
    }
    response.set_cookie(
        settings.security.access_token_cookie_name,
        access_token,
        **cookie_kwargs,
    )
    response.set_cookie(
        settings.security.refresh_token_cookie_name,
        refresh_token,
        **cookie_kwargs,
    )


def clear_auth_cookies(response: RedirectResponse) -> None:
    """Удалить аутентификационные cookie из ответа.

    Args:
        response: Ответ, из которого удаляются cookie.
    """
    cookie_kwargs = {
        "samesite": settings.security.cookie_samesite,
        "secure": settings.security.cookie_secure,
        "path": "/",
    }
    response.delete_cookie(
        settings.security.access_token_cookie_name,
        **cookie_kwargs,
    )
    response.delete_cookie(
        settings.security.refresh_token_cookie_name,
        **cookie_kwargs,
    )
