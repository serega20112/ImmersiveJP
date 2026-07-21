from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse

from src.backend.delivery.api.v1.helpers import (
    clear_auth_cookies,
    redirect_to_route,
    set_auth_cookies,
)
from src.backend.dependencies.service_dependencies import AuthServiceDependency
from src.backend.dto.auth_dto import LoginDTO, RegistrationDTO, VerificationDTO
from src.backend.infrastructure.web import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    flash,
    render_template,
)
from src.backend.use_case.auth.login_user import EmailNotVerifiedError, InvalidCredentialsError
from src.backend.use_case.auth.register_user import (
    EmailAlreadyExistsError,
    InvalidRegistrationDataError,
)
from src.backend.use_case.auth.verify_email import InvalidVerificationCodeError

auth_router = APIRouter(prefix="/auth")


@auth_router.get("/register", name="auth.register_page")
async def register_page(request: Request):
    """Render the registration page.

    Args:
        request: The incoming request.

    Returns:
        The rendered registration template.
    """
    return await render_template(request, "auth/register.html")


@auth_router.post("/register", name="auth.register_user")
async def register_user(
    request: Request,
    auth_service: AuthServiceDependency,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    display_name: Annotated[str, Form()],
):
    """Handle user registration form submission.

    Args:
        request: The incoming request.
        auth_service: The auth service dependency.
        email: The user's email address.
        password: The user's password.
        display_name: The user's display name.

    Returns:
        A redirect response.
    """
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
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except (EmailAlreadyExistsError, InvalidRegistrationDataError) as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "auth.register_page")


@auth_router.get("/login", name="auth.login_page")
async def login_page(request: Request):
    """Render the login page.

    Args:
        request: The incoming request.

    Returns:
        The rendered login template.
    """
    return await render_template(request, "auth/login.html")


@auth_router.post("/login", name="auth.login_user")
async def login_user(
    request: Request,
    auth_service: AuthServiceDependency,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    """Handle user login form submission.

    Args:
        request: The incoming request.
        auth_service: The auth service dependency.
        email: The user's email address.
        password: The user's password.

    Returns:
        A redirect response with auth cookies.
    """
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
async def logout_user(request: Request, auth_service: AuthServiceDependency):
    """Handle user logout.

    Args:
        request: The incoming request.
        auth_service: The auth service dependency.

    Returns:
        A redirect response with cleared auth cookies.
    """
    await auth_service.logout(
        request.cookies.get(ACCESS_TOKEN_COOKIE_NAME),
        request.cookies.get(REFRESH_TOKEN_COOKIE_NAME),
    )
    response = redirect_to_route(request, "index.landing")
    clear_auth_cookies(response)
    return response


@auth_router.get("/verify-email", name="auth.verify_email_page")
async def verify_email_page(request: Request):
    """Render the email verification page.

    Args:
        request: The incoming request.

    Returns:
        The rendered verification template.
    """
    return await render_template(
        request,
        "auth/verify_email.html",
        email=str(request.query_params.get("email") or ""),
    )


@auth_router.post("/verify-email", name="auth.verify_email")
async def verify_email(
    request: Request,
    auth_service: AuthServiceDependency,
    email: Annotated[str, Form()],
    code: Annotated[str, Form()],
):
    """Handle email verification form submission.

    Args:
        request: The incoming request.
        auth_service: The auth service dependency.
        email: The user's email address.
        code: The verification code.

    Returns:
        A redirect response.
    """
    try:
        await auth_service.verify_email(VerificationDTO(email=email, code=code))
        flash(request, "Почта подтверждена. Теперь можно войти.", "success")
        return redirect_to_route(request, "auth.login_page")
    except InvalidVerificationCodeError as error:
        flash(request, str(error), "error")
        return RedirectResponse(
            url=f"{request.app.url_path_for('auth.verify_email_page')}?email={email}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
