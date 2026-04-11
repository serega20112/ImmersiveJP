from __future__ import annotations

from fastapi.responses import RedirectResponse

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.web import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
)


def set_auth_cookies(
    response: RedirectResponse,
    access_token: str,
    refresh_token: str,
) -> None:
    cookie_kwargs = {
        "httponly": True,
        "samesite": Settings.cookie_samesite,
        "secure": Settings.cookie_secure,
        "path": "/",
    }
    response.set_cookie(ACCESS_TOKEN_COOKIE_NAME, access_token, **cookie_kwargs)
    response.set_cookie(REFRESH_TOKEN_COOKIE_NAME, refresh_token, **cookie_kwargs)


def clear_auth_cookies(response: RedirectResponse) -> None:
    cookie_kwargs = {
        "samesite": Settings.cookie_samesite,
        "secure": Settings.cookie_secure,
        "path": "/",
    }
    response.delete_cookie(ACCESS_TOKEN_COOKIE_NAME, **cookie_kwargs)
    response.delete_cookie(REFRESH_TOKEN_COOKIE_NAME, **cookie_kwargs)
