from __future__ import annotations

from functools import cached_property

from src.backend.services import OnboardingService
from src.backend.use_case.onboarding import (
    CompleteOnboardingUseCase,
    GetOnboardingPageUseCase,
)


class OnboardingProvidersMixin:
    @cached_property
    def get_onboarding_page_use_case(self) -> GetOnboardingPageUseCase:
        return GetOnboardingPageUseCase()

    @cached_property
    def complete_onboarding_use_case(self) -> CompleteOnboardingUseCase:
        return CompleteOnboardingUseCase(
            self.user_repository,
            self.generate_cards_use_case,
        )

    @cached_property
    def onboarding_service(self) -> OnboardingService:
        return OnboardingService(
            self.complete_onboarding_use_case,
            self.get_onboarding_page_use_case,
        )
