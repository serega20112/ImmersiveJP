"""Роуты выхода пользователя."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.config.settings import settings
from src.infrastructures.di_containers.service_dependencies import AuthServiceDependency
from src.presentation.http import clear_auth_cookies, redirect_to_route

logout_router = APIRouter()


@logout_router.post("/logout", name="auth.logout_user")
async def logout_user(
    request: Request,
    auth_service: AuthServiceDependency,
) -> RedirectResponse:
    """Обработать выход пользователя.

    Args:
        request: Входящий запрос.
        auth_service: Сервис аутентификации.

    Returns:
        Редирект на главную с очищенными auth-cookie.
    """
    await auth_service.logout(
        request.cookies.get(settings.security.access_token_cookie_name),
        request.cookies.get(settings.security.refresh_token_cookie_name),
    )
    response = redirect_to_route(request, "index.landing")
    clear_auth_cookies(response)
    return response
