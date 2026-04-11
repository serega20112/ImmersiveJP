from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request

from src.backend.dependencies.auth_dependencies import require_registered_user
from src.backend.dependencies.service_dependencies import OnboardingServiceDependency
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.dto.onboarding_dto import OnboardingDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template
from src.backend.use_case.onboarding.complete_onboarding import (
    InvalidOnboardingDataError,
)

onboarding_router = APIRouter()


@onboarding_router.get("/onboarding", name="onboarding.page")
async def onboarding_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_registered_user)],
    onboarding_service: OnboardingServiceDependency,
):
    if current_user.onboarding_completed:
        return redirect_to_route(request, "dashboard.dashboard_page")
    page = await onboarding_service.get_page()
    return await render_template(request, "onboarding/index.html", page=page)


@onboarding_router.post("/onboarding", name="onboarding.complete")
async def complete_onboarding(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_registered_user)],
    onboarding_service: OnboardingServiceDependency,
):
    form = await request.form()
    diagnostic_answers = {
        key.removeprefix("diagnostic_"): str(value)
        for key, value in form.items()
        if key.startswith("diagnostic_")
    }
    try:
        result = await onboarding_service.complete(
            current_user.id,
            OnboardingDTO(
                goal=str(form.get("goal", "")),
                language_level=str(form.get("language_level", "")),
                study_timeline=str(form.get("study_timeline", "")),
                interests_text=str(form.get("interests_text", "")),
                diagnostic_answers=diagnostic_answers,
                diagnostic_hints_used=int(
                    str(form.get("diagnostic_hints_used", "0")) or 0
                ),
            ),
        )
        flash(request, result.skill_assessment.summary, "success")
        flash(
            request,
            "Стартовые карточки готовы. Переходим сразу к первому блоку.",
            "success",
        )
        return redirect_to_route(request, "learning.language")
    except InvalidOnboardingDataError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "onboarding.page")
