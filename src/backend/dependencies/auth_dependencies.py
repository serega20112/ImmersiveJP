from __future__ import annotations

from fastapi import Request

from src.backend.dependencies.current_user import get_current_user, resolve_current_user
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import RouteRedirectError


def _redirect(request: Request, route_name: str) -> RouteRedirectError:
    return RouteRedirectError(request.app.url_path_for(route_name))


async def require_registered_user(request: Request) -> UserViewDTO:
    current_user = get_current_user(request) or await resolve_current_user(request)
    if current_user is None:
        raise _redirect(request, "auth.register_page")
    return current_user


async def require_authenticated_user(request: Request) -> UserViewDTO:
    current_user = get_current_user(request) or await resolve_current_user(request)
    if current_user is None:
        raise _redirect(request, "auth.login_page")
    return current_user


async def require_onboarded_user(
    request: Request,
) -> UserViewDTO:
    current_user = await require_authenticated_user(request)
    if not current_user.onboarding_completed:
        raise _redirect(request, "onboarding.page")
    return current_user
