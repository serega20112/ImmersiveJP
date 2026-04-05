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
        interests = self._parse_interests(payload.interests_text)
        if not interests:
            raise InvalidOnboardingDataError("Нужно указать хотя бы один интерес")

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

    @staticmethod
    def _parse_interests(raw_value: str) -> list[str]:
        prepared = raw_value.replace("\r", "\n").replace(";", ",")
        items: list[str] = []
        seen: set[str] = set()
        for chunk in prepared.split("\n"):
            for part in chunk.split(","):
                value = part.strip()
                normalized = value.casefold()
                if not value or normalized in seen:
                    continue
                seen.add(normalized)
                items.append(value)
        return items
