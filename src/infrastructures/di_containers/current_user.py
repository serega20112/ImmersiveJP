from __future__ import annotations

from fastapi import Request

from src.application.dto.auth import UserViewDTO
from src.config.settings import settings
from src.infrastructures.di_containers.request_scope import _UNRESOLVED_CURRENT_USER
from src.infrastructures.di_containers.service_dependencies import get_auth_service


def get_current_user(request: Request) -> UserViewDTO | None:
    current_user = getattr(request.state, "current_user", None)
    if current_user is _UNRESOLVED_CURRENT_USER:
        return None
    return current_user


async def resolve_current_user(request: Request) -> UserViewDTO | None:
    current_user = getattr(request.state, "current_user", None)
    if current_user is not _UNRESOLVED_CURRENT_USER:
        return current_user

    access_token = request.cookies.get(settings.security.access_token_cookie_name)
    try:
        auth_service = get_auth_service()
    except RuntimeError:
        request.state.current_user = None
        return None

    resolved = await auth_service.resolve_current_user(access_token)
    request.state.current_user = resolved
    return resolved
