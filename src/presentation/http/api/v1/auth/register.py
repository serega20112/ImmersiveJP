"""Роуты регистрации пользователя."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.application.dto.auth import RegistrationDTO
from src.infrastructures.di_containers.service_dependencies import AuthServiceDependency
from src.presentation.http import flash, render_template
from src.presentation.http.schemas import RegistrationForm

register_router = APIRouter()


@register_router.get("/register", name="auth.register_page")
async def register_page(request: Request) -> HTMLResponse:
    """Отрисовать страницу регистрации.

    Args:
        request: Входящий запрос.

    Returns:
        Ответ с шаблоном регистрации.
    """
    return await render_template(request, "auth/register.html")


@register_router.post("/register", name="auth.register_user")
async def register_user(
    request: Request,
    auth_service: AuthServiceDependency,
    form: Annotated[RegistrationForm, Form()],
) -> RedirectResponse:
    """Обработать отправку формы регистрации.

    Args:
        request: Входящий запрос.
        auth_service: Сервис аутентификации.
        form: Данные формы регистрации.

    Returns:
        Редирект на страницу подтверждения email.

    Ошибки некорректных данных обрабатываются глобальными обработчиками.
    """
    await auth_service.register(
        RegistrationDTO(
            email=form.email,
            password=form.password,
            display_name=form.display_name,
        )
    )
    flash(
        request,
        "Аккаунт создан. Мы отправили код подтверждения на почту.",
        "success",
    )
    return RedirectResponse(
        url=f"{request.app.url_path_for('auth.verify_email_page')}?email={form.email}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
