from __future__ import annotations

from src.backend.dto.onboarding_dto import OnboardingDTO, OnboardingResultDTO
from src.backend.use_case.onboarding import CompleteOnboardingUseCase


class OnboardingService:
    def __init__(self, complete_onboarding_use_case: CompleteOnboardingUseCase):
        self._complete_onboarding_use_case = complete_onboarding_use_case

    async def complete(
        self, user_id: int, payload: OnboardingDTO
    ) -> OnboardingResultDTO:
        return await self._complete_onboarding_use_case.execute(user_id, payload)
