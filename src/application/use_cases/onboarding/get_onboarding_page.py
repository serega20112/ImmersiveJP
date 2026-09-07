from __future__ import annotations

from src.application.dto.onboarding import OnboardingPageDTO
from src.application.use_cases.onboarding.diagnostic_questions import (
    build_onboarding_question_groups,
    build_study_timeline_options,
)


class GetOnboardingPageUseCase:
    async def execute(self) -> OnboardingPageDTO:
        """Get the onboarding page with diagnostic questions.

        Returns:
            The onboarding page data.
        """
        return OnboardingPageDTO(
            diagnostic_groups=build_onboarding_question_groups(),
            study_timeline_options=build_study_timeline_options(),
        )
