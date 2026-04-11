from __future__ import annotations

import pytest

from src.backend.infrastructure.cache import KeyValueStore
from src.backend.services.onboarding_service import OnboardingService
from src.backend.dto.onboarding_dto import (
    OnboardingPageDTO,
    StudyTimelineOptionDTO,
)


class _StubCompleteOnboardingUseCase:
    async def execute(self, user_id: int, payload):  # pragma: no cover
        raise NotImplementedError


class _StubGetOnboardingPageUseCase:
    def __init__(self):
        self.calls = 0

    async def execute(self) -> OnboardingPageDTO:
        self.calls += 1
        return OnboardingPageDTO(
            study_timeline_options=[
                StudyTimelineOptionDTO(
                    value="steady",
                    title="Steady",
                    description="A steady weekly plan.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_onboarding_page_is_loaded_from_cache_after_first_request():
    page_use_case = _StubGetOnboardingPageUseCase()
    service = OnboardingService(
        _StubCompleteOnboardingUseCase(),
        page_use_case,
        KeyValueStore(redis_url=None, namespace="test-onboarding-cache"),
    )

    first = await service.get_page()
    second = await service.get_page()

    assert first == second
    assert page_use_case.calls == 1
