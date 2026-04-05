from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.domain.user import LanguageLevel, LearningGoal
from src.backend.dto.onboarding_dto import OnboardingDTO, OnboardingResultDTO
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.learning.generate_cards import GenerateCardsUseCase


class InvalidOnboardingDataError(Exception):
    pass


class CompleteOnboardingUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        generate_cards_use_case: GenerateCardsUseCase,
    ):
        self._user_repository = user_repository
        self._generate_cards_use_case = generate_cards_use_case

    async def execute(
        self, user_id: int, payload: OnboardingDTO
    ) -> OnboardingResultDTO:
        try:
            goal = LearningGoal(payload.goal)
            language_level = LanguageLevel(payload.language_level)
        except ValueError as error:
            raise InvalidOnboardingDataError("Некорректная цель или уровень") from error
        interests = [item.strip() for item in payload.interests if item.strip()]
        if not interests:
            raise InvalidOnboardingDataError("Нужно выбрать хотя бы один интерес")

        await self._user_repository.update_learning_profile(
            user_id=user_id,
            goal=goal,
            language_level=language_level,
            interests=interests,
        )
        generated_batches: dict[str, int] = {}
        for track in TrackType:
            await self._generate_cards_use_case.execute(user_id, track)
            generated_batches[track.value] = 1
        return OnboardingResultDTO(user_id=user_id, generated_batches=generated_batches)
