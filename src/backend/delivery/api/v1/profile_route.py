from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request

from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dependencies.auth_dependencies import require_authenticated_user
from src.backend.dependencies.service_dependencies import ProfileServiceDependency
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash, render_template
from src.backend.use_case.profile import InvalidMentorMessageError

profile_router = APIRouter()


@profile_router.get("/profile", name="profile.page")
async def profile_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
):
    """Render the profile page with progress and advice.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        profile_service: The profile service dependency.

    Returns:
        The rendered profile template.
    """
    report = await profile_service.build_progress_report(current_user.id)
    advice = await profile_service.generate_ai_advice(current_user.id, report)
    return await render_template(request, "profile/index.html", report=report, advice=advice)


@profile_router.get("/plan", name="profile.plan_page")
async def plan_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
):
    """Render the learning plan page.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        profile_service: The profile service dependency.

    Returns:
        The rendered plan template.
    """
    page = await profile_service.build_learning_plan(current_user.id)
    return await render_template(request, "profile/plan.html", page=page)


@profile_router.get("/mentor", name="profile.mentor_page")
async def mentor_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
):
    """Render the mentor page.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        profile_service: The profile service dependency.

    Returns:
        The rendered mentor template.
    """
    page = await profile_service.get_mentor_page(current_user.id)
    return await render_template(request, "profile/mentor.html", page=page)


@profile_router.post("/mentor", name="profile.mentor_send")
async def mentor_send(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_authenticated_user)],
    profile_service: ProfileServiceDependency,
    message: str = Form(),
):
    """Handle sending a mentor message.

    Args:
        request: The incoming request.
        current_user: The authenticated user.
        profile_service: The profile service dependency.
        message: The message text.

    Returns:
        The rendered mentor template or a redirect.
    """
    try:
        page = await profile_service.send_mentor_message(current_user.id, message)
        return await render_template(request, "profile/mentor.html", page=page)
    except InvalidMentorMessageError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "profile.mentor_page")
