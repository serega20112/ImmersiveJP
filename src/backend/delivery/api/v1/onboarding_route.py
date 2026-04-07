from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request

from src.backend.delivery.api.v1.helpers import get_current_user
from src.backend.delivery.api.v1.helpers import get_onboarding_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dto.onboarding_dto import OnboardingDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template
from src.backend.use_case.onboarding.complete_onboarding import (
    InvalidOnboardingDataError,
)

onboarding_router = APIRouter()


@onboarding_router.get("/onboarding", name="onboarding.page")
async def onboarding_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.register_page")
    if current_user.onboarding_completed:
        return redirect_to_route(request, "dashboard.dashboard_page")
    page = await get_onboarding_service(request).get_page()
    return render_template(request, "onboarding/index.html", page=page)


@onboarding_router.post("/onboarding", name="onboarding.complete")
async def complete_onboarding(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.register_page")

    form = await request.form()
    diagnostic_answers = {
        key.removeprefix("diagnostic_"): str(value)
        for key, value in form.items()
        if key.startswith("diagnostic_")
    }
    try:
        result = await get_onboarding_service(request).complete(
            current_user.id,
            OnboardingDTO(
                goal=str(form.get("goal", "")),
                language_level=str(form.get("language_level", "")),
                study_timeline=str(form.get("study_timeline", "")),
                interests_text=str(form.get("interests_text", "")),
                diagnostic_answers=diagnostic_answers,
                diagnostic_hints_used=int(str(form.get("diagnostic_hints_used", "0")) or 0),
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
