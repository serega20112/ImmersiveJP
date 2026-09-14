"""Роуты входа пользователя."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.application.dto.auth import LoginDTO
from src.infrastructures.di_containers.service_dependencies import AuthServiceDependency
from src.presentation.http import (
    flash,
    redirect_to_route,
    render_template,
    set_auth_cookies,
)
from src.presentation.http.schemas import LoginForm

login_router = APIRouter()


@login_router.get("/login", name="auth.login_page")
async def login_page(request: Request) -> HTMLResponse:
    """Отрисовать страницу входа.

    Args:
        request: Входящий запрос.

    Returns:
        Ответ с шаблоном входа.
    """
    return await render_template(request, "auth/login.html")


@login_router.post("/login", name="auth.login_user")
async def login_user(
    request: Request,
    auth_service: AuthServiceDependency,
    form: Annotated[LoginForm, Form()],
) -> RedirectResponse:
    """Обработать отправку формы входа.

    Args:
        request: Входящий запрос.
        auth_service: Сервис аутентификации.
        form: Данные формы входа.

    Returns:
        Редирект на дашборд с auth-cookie.

    Ошибки некорректных учётных данных обрабатываются глобальными обработчиками.
    """
    auth_result = await auth_service.login(LoginDTO(email=form.email, password=form.password))
    flash(request, f"С возвращением, {auth_result.user.display_name}.", "success")
    response = redirect_to_route(request, "dashboard.dashboard_page")
    set_auth_cookies(
        response, auth_result.tokens.access_token, auth_result.tokens.refresh_token
    )
    return response
