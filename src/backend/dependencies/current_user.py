from __future__ import annotations

from fastapi import Request

from src.backend.dependencies.request_scope import _UNRESOLVED_CURRENT_USER
from src.backend.dependencies.service_dependencies import get_auth_service
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web.constants import ACCESS_TOKEN_COOKIE_NAME


def get_current_user(request: Request) -> UserViewDTO | None:
    current_user = getattr(request.state, "current_user", None)
    if current_user is _UNRESOLVED_CURRENT_USER:
        return None
    return current_user


async def resolve_current_user(request: Request) -> UserViewDTO | None:
    current_user = getattr(request.state, "current_user", None)
    if current_user is not _UNRESOLVED_CURRENT_USER:
        return current_user

    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    try:
        auth_service = get_auth_service()
    except RuntimeError:
        request.state.current_user = None
        return None

    resolved = await auth_service.resolve_current_user(access_token)
    request.state.current_user = resolved
    return resolved
