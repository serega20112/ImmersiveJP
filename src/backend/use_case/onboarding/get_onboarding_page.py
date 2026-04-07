from __future__ import annotations

from src.backend.dto.onboarding_dto import OnboardingPageDTO
from src.backend.use_case.onboarding.diagnostic_questions import (
    build_onboarding_question_groups,
    build_study_timeline_options,
)


class GetOnboardingPageUseCase:
    async def execute(self) -> OnboardingPageDTO:
        return OnboardingPageDTO(
            diagnostic_groups=build_onboarding_question_groups(),
            study_timeline_options=build_study_timeline_options(),
        )
