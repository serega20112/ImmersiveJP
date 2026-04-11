from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request
from fastapi.responses import RedirectResponse

from src.backend.delivery.api.v1.helpers import clear_auth_cookies
from src.backend.delivery.api.v1.helpers import get_auth_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.delivery.api.v1.helpers import set_auth_cookies
from src.backend.dto.auth_dto import LoginDTO
from src.backend.dto.auth_dto import RegistrationDTO
from src.backend.dto.auth_dto import VerificationDTO
from src.backend.infrastructure.web import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    flash,
    render_template,
)
from src.backend.use_case.auth.login_user import EmailNotVerifiedError
from src.backend.use_case.auth.login_user import InvalidCredentialsError
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError
from src.backend.use_case.auth.register_user import InvalidRegistrationDataError
from src.backend.use_case.auth.verify_email import InvalidVerificationCodeError

auth_router = APIRouter(prefix="/auth")


@auth_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    return render_template(request, "auth/register.html")


@auth_router.post("/register", name="auth.register_user")
async def register_user(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
):
    auth_service = get_auth_service(request)
    try:
        await auth_service.register(
            RegistrationDTO(
                email=email,
                password=password,
                display_name=display_name,
            )
        )
        flash(
            request,
            "Аккаунт создан. Мы отправили код подтверждения на почту.",
            "success",
        )
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
    except (EmailAlreadyExistsError, InvalidRegistrationDataError) as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "auth.register_page")


@auth_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    return render_template(request, "auth/login.html")


@auth_router.post("/login", name="auth.login_user")
async def login_user(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    auth_service = get_auth_service(request)
    try:
        auth_result = await auth_service.login(LoginDTO(email=email, password=password))
        flash(request, f"С возвращением, {auth_result.user.display_name}.", "success")
        response = redirect_to_route(request, "dashboard.dashboard_page")
        set_auth_cookies(
            response, auth_result.tokens.access_token, auth_result.tokens.refresh_token
        )
        return response
    except (InvalidCredentialsError, EmailNotVerifiedError) as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "auth.login_page")


@auth_router.post("/logout", name="auth.logout_user")
async def logout_user(request: Request):
    auth_service = get_auth_service(request)
    await auth_service.logout(
        request.cookies.get(ACCESS_TOKEN_COOKIE_NAME),
        request.cookies.get(REFRESH_TOKEN_COOKIE_NAME),
    )
    response = redirect_to_route(request, "index.landing")
    clear_auth_cookies(response)
    return response


@auth_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request):
    return render_template(
        request,
        "auth/verify_email.html",
        email=str(request.query_params.get("email") or ""),
    )


@auth_router.post("/verify-email", name="auth.verify_email")
async def verify_email(
    request: Request,
    email: Annotated[str, Form()],
    code: Annotated[str, Form()],
):
    auth_service = get_auth_service(request)
    try:
        await auth_service.verify_email(VerificationDTO(email=email, code=code))
        flash(request, "Почта подтверждена. Теперь можно войти.", "success")
        return redirect_to_route(request, "auth.login_page")
    except InvalidVerificationCodeError as error:
        flash(request, str(error), "error")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=303,
        )
