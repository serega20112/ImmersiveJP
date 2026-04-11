from __future__ import annotations

from fastapi import Request

from src.backend.dependencies.current_user import get_current_user, resolve_current_user
from src.backend.dependencies.service_dependencies import (
    get_auth_service as _get_auth_service,
)
from src.backend.dependencies.service_dependencies import (
    get_dashboard_service as _get_dashboard_service,
)
from src.backend.dependencies.service_dependencies import (
    get_learning_service as _get_learning_service,
)
from src.backend.dependencies.service_dependencies import (
    get_onboarding_service as _get_onboarding_service,
)
from src.backend.dependencies.service_dependencies import (
    get_profile_service as _get_profile_service,
)
from src.backend.services import (
    AuthServiceContract,
    DashboardServiceContract,
    LearningServiceContract,
    OnboardingServiceContract,
    ProfileServiceContract,
)


def get_auth_service(_request: Request | None = None) -> AuthServiceContract:
    return _get_auth_service()


def get_onboarding_service(
    _request: Request | None = None,
) -> OnboardingServiceContract:
    return _get_onboarding_service()


def get_dashboard_service(_request: Request | None = None) -> DashboardServiceContract:
    return _get_dashboard_service()


def get_learning_service(_request: Request | None = None) -> LearningServiceContract:
    return _get_learning_service()


def get_profile_service(_request: Request | None = None) -> ProfileServiceContract:
    return _get_profile_service()
