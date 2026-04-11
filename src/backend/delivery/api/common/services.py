from __future__ import annotations

from fastapi import Request

from src.backend.dto.auth_dto import UserViewDTO
from src.backend.services import (
    AuthService,
    DashboardService,
    LearningService,
    OnboardingService,
    ProfileService,
)


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
