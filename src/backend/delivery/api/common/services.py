from __future__ import annotations

from fastapi import Request

from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import ACCESS_TOKEN_COOKIE_NAME
from src.backend.services import (
    AuthService,
    DashboardService,
    LearningService,
    OnboardingService,
    ProfileService,
)

_UNRESOLVED_CURRENT_USER = object()


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
    current_user = getattr(request.state, "current_user", None)
    if current_user is _UNRESOLVED_CURRENT_USER:
        return None
    return current_user


async def resolve_current_user(request: Request) -> UserViewDTO | None:
    current_user = getattr(request.state, "current_user", None)
    if current_user is not _UNRESOLVED_CURRENT_USER:
        return current_user

    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    resolved = await request.state.container.auth_service.resolve_current_user(
        access_token
    )
    request.state.current_user = resolved
    return resolved
