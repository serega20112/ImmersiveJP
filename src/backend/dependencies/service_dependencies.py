from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.backend.dependencies.request_scope import get_request_container
from src.backend.services import (
    AuthServiceContract,
    DashboardServiceContract,
    LearningServiceContract,
    OnboardingServiceContract,
    ProfileServiceContract,
)


def get_auth_service() -> AuthServiceContract:
    return get_request_container().auth_service


def get_onboarding_service() -> OnboardingServiceContract:
    return get_request_container().onboarding_service


def get_dashboard_service() -> DashboardServiceContract:
    return get_request_container().dashboard_service


def get_learning_service() -> LearningServiceContract:
    return get_request_container().learning_service


def get_profile_service() -> ProfileServiceContract:
    return get_request_container().profile_service


AuthServiceDependency = Annotated[AuthServiceContract, Depends(get_auth_service)]
OnboardingServiceDependency = Annotated[
    OnboardingServiceContract, Depends(get_onboarding_service)
]
DashboardServiceDependency = Annotated[
    DashboardServiceContract, Depends(get_dashboard_service)
]
LearningServiceDependency = Annotated[
    LearningServiceContract, Depends(get_learning_service)
]
ProfileServiceDependency = Annotated[
    ProfileServiceContract, Depends(get_profile_service)
]
