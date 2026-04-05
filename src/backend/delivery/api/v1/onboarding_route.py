from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Form
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
    return render_template(request, "onboarding/index.html")


@onboarding_router.post("/onboarding", name="onboarding.complete")
async def complete_onboarding(
    request: Request,
    goal: Annotated[str, Form()],
    language_level: Annotated[str, Form()],
    interests_text: Annotated[str, Form()],
):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.register_page")
    try:
        await get_onboarding_service(request).complete(
            current_user.id,
            OnboardingDTO(
                goal=goal,
                language_level=language_level,
                interests_text=interests_text,
            ),
        )
        flash(request, "Стартовые карточки готовы. Переходим сразу к первому блоку.", "success")
        return redirect_to_route(request, "learning.language")
    except InvalidOnboardingDataError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "onboarding.page")
