from __future__ import annotations

from fastapi import Request

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
    """Get the auth service instance.

    Args:
        _request: Optional request object (unused).

    Returns:
        The auth service instance.
    """
    return _get_auth_service()


def get_onboarding_service(
    _request: Request | None = None,
) -> OnboardingServiceContract:
    """Get the onboarding service instance.

    Args:
        _request: Optional request object (unused).

    Returns:
        The onboarding service instance.
    """
    return _get_onboarding_service()


def get_dashboard_service(_request: Request | None = None) -> DashboardServiceContract:
    """Get the dashboard service instance.

    Args:
        _request: Optional request object (unused).

    Returns:
        The dashboard service instance.
    """
    return _get_dashboard_service()


def get_learning_service(_request: Request | None = None) -> LearningServiceContract:
    """Get the learning service instance.

    Args:
        _request: Optional request object (unused).

    Returns:
        The learning service instance.
    """
    return _get_learning_service()


def get_profile_service(_request: Request | None = None) -> ProfileServiceContract:
    """Get the profile service instance.

    Args:
        _request: Optional request object (unused).

    Returns:
        The profile service instance.
    """
    return _get_profile_service()
