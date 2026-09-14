"""Роуты подтверждения email."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from src.application.dto.auth import VerificationDTO
from src.infrastructures.di_containers.service_dependencies import AuthServiceDependency
from src.presentation.http import flash, redirect_to_route, render_template
from src.presentation.http.schemas import VerificationForm

verification_router = APIRouter()


@verification_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request) -> HTMLResponse:
    """Отрисовать страницу подтверждения email.

    Args:
        request: Входящий запрос.

    Returns:
        Ответ с шаблоном подтверждения.
    """
    return await render_template(
        request,
        "auth/verify_email.html",
        email=str(request.query_params.get("email") or ""),
    )


@verification_router.post("/verify-email", name="auth.verify_email")
async def verify_email(
    request: Request,
    auth_service: AuthServiceDependency,
    form: Annotated[VerificationForm, Form()],
) -> RedirectResponse:
    """Обработать отправку кода подтверждения.

    Args:
        request: Входящий запрос.
        auth_service: Сервис аутентификации.
        form: Данные формы подтверждения.

    Returns:
        Редирект на страницу входа.

    Ошибки неверного кода обрабатываются глобальными обработчиками.
    """
    await auth_service.verify_email(VerificationDTO(email=form.email, code=form.code))
    flash(request, "Почта подтверждена. Теперь можно войти.", "success")
    return redirect_to_route(request, "auth.login_page")
