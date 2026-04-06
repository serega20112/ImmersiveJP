from __future__ import annotations

from src.backend.dto.onboarding_dto import (
    OnboardingDTO,
    OnboardingPageDTO,
    OnboardingResultDTO,
)
from src.backend.use_case.onboarding import (
    CompleteOnboardingUseCase,
    GetOnboardingPageUseCase,
)


class OnboardingService:
    def __init__(
        self,
        complete_onboarding_use_case: CompleteOnboardingUseCase,
        get_onboarding_page_use_case: GetOnboardingPageUseCase,
    ):
        self._complete_onboarding_use_case = complete_onboarding_use_case
        self._get_onboarding_page_use_case = get_onboarding_page_use_case

    async def get_page(self) -> OnboardingPageDTO:
        return await self._get_onboarding_page_use_case.execute()

    async def complete(
        self, user_id: int, payload: OnboardingDTO
    ) -> OnboardingResultDTO:
        return await self._complete_onboarding_use_case.execute(user_id, payload)
