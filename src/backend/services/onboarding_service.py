from __future__ import annotations

from src.backend.infrastructure.cache import KeyValueStore
from src.backend.dependencies.settings import Settings
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
        cache_store: KeyValueStore,
    ):
        self._complete_onboarding_use_case = complete_onboarding_use_case
        self._get_onboarding_page_use_case = get_onboarding_page_use_case
        self._cache_store = cache_store

    async def get_page(self) -> OnboardingPageDTO:
        cache_ttl = Settings.onboarding_page_cache_ttl_seconds
        cache_key = "onboarding:page"
        cached_page = await self._cache_store.get_json(cache_key)
        if cached_page is not None:
            return OnboardingPageDTO.model_validate(cached_page)

        page = await self._get_onboarding_page_use_case.execute()
        await self._cache_store.set_json(
            cache_key,
            page.model_dump(mode="json"),
            expire_seconds=cache_ttl,
        )
        return page

    async def complete(
        self, user_id: int, payload: OnboardingDTO
    ) -> OnboardingResultDTO:
        return await self._complete_onboarding_use_case.execute(user_id, payload)
