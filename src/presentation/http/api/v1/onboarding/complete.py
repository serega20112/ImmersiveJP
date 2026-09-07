"""Роут завершения онбординга."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.application.dto.onboarding import OnboardingDTO
from src.infrastructures.di_containers.auth_dependencies import require_registered_user
from src.infrastructures.di_containers.service_dependencies import OnboardingServiceDependency
from src.presentation.http import flash, redirect_to_route
from src.presentation.http.schemas import OnboardingForm

onboarding_complete_router = APIRouter()


@onboarding_complete_router.post("/onboarding", name="onboarding.complete")
async def complete_onboarding(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_registered_user)],
    onboarding_service: OnboardingServiceDependency,
    form: Annotated[OnboardingForm, Depends()],
) -> RedirectResponse:
    """Обработать отправку формы онбординга.

    Args:
        request: Входящий запрос.
        current_user: Зарегистрированный пользователь.
        onboarding_service: Сервис онбординга.
        form: Данные формы онбординга.

    Returns:
        Редирект на первый урок.

    Ошибки некорректных данных обрабатываются глобальными обработчиками.
    """
    raw_form = await request.form()
    diagnostic_answers = {
        key.removeprefix("diagnostic_"): str(value)
        for key, value in raw_form.items()
        if key.startswith("diagnostic_")
    }
    result = await onboarding_service.complete(
        current_user.id,
        OnboardingDTO(
            goal=form.goal,
            language_level=form.language_level,
            study_timeline=form.study_timeline,
            interests_text=form.interests_text,
            diagnostic_answers=diagnostic_answers,
            diagnostic_hints_used=form.diagnostic_hints_used,
        ),
    )
    flash(request, result.skill_assessment.summary, "success")
    flash(request, "Стартовые карточки готовы. Переходим сразу к первому блоку.", "success")
    return redirect_to_route(request, "learning.language")
