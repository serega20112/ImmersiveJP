from __future__ import annotations

from fastapi.responses import RedirectResponse

from src.backend.dependencies.settings import Settings


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
    response.set_cookie("access_token", access_token, **cookie_kwargs)
    response.set_cookie("refresh_token", refresh_token, **cookie_kwargs)


def clear_auth_cookies(response: RedirectResponse) -> None:
    cookie_kwargs = {
        "samesite": Settings.cookie_samesite,
        "secure": Settings.cookie_secure,
        "path": "/",
    }
    response.delete_cookie("access_token", **cookie_kwargs)
    response.delete_cookie("refresh_token", **cookie_kwargs)
