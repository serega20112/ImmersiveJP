from __future__ import annotations

from src.backend.dto.onboarding_dto import OnboardingPageDTO
from src.backend.use_case.onboarding.diagnostic_questions import (
    build_onboarding_questions,
)


class GetOnboardingPageUseCase:
    async def execute(self) -> OnboardingPageDTO:
        return OnboardingPageDTO(diagnostic_questions=build_onboarding_questions())
