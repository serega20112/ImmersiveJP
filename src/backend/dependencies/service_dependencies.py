from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.backend.dependencies.request_scope import get_request_container
from src.backend.services import (
    AuthService,
    DashboardService,
    LearningService,
    OnboardingService,
    ProfileService,
)


def get_auth_service() -> AuthService:
    return get_request_container().auth_service


def get_onboarding_service() -> OnboardingService:
    return get_request_container().onboarding_service


def get_dashboard_service() -> DashboardService:
    return get_request_container().dashboard_service


def get_learning_service() -> LearningService:
    return get_request_container().learning_service


def get_profile_service() -> ProfileService:
    return get_request_container().profile_service


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
OnboardingServiceDependency = Annotated[
    OnboardingService, Depends(get_onboarding_service)
]
DashboardServiceDependency = Annotated[
    DashboardService, Depends(get_dashboard_service)
]
LearningServiceDependency = Annotated[LearningService, Depends(get_learning_service)]
ProfileServiceDependency = Annotated[ProfileService, Depends(get_profile_service)]
