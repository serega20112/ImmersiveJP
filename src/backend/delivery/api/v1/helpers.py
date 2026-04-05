from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse

from src.backend.dependencies.settings import Settings
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.services import AuthService
from src.backend.services import DashboardService
from src.backend.services import LearningService
from src.backend.services import OnboardingService
from src.backend.services import ProfileService


def get_auth_service(request: Request) -> AuthService:
    return request.state.container.auth_service


def get_onboarding_service(request: Request) -> OnboardingService:
    return request.state.container.onboarding_service


def get_dashboard_service(request: Request) -> DashboardService:
    return request.state.container.dashboard_service


def get_learning_service(request: Request) -> LearningService:
    return request.state.container.learning_service


def get_profile_service(request: Request) -> ProfileService:
    return request.state.container.profile_service


def get_current_user(request: Request) -> UserViewDTO | None:
    return getattr(request.state, "current_user", None)


def redirect_to_route(request: Request, route_name: str) -> RedirectResponse:
    return RedirectResponse(url=request.app.url_path_for(route_name), status_code=303)


def track_href(track: str) -> str:
    return {
        "language": "/learn/language",
        "culture": "/learn/culture",
        "history": "/learn/history",
    }[track]


def resolve_return_to(return_to: str | None, fallback: str) -> str:
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return fallback


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
