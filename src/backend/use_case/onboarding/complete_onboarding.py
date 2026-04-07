from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.domain.user import LanguageLevel, LearningGoal, StudyTimeline
from src.backend.dto.onboarding_dto import OnboardingDTO, OnboardingResultDTO
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.learning.generate_cards import GenerateCardsUseCase
from src.backend.use_case.mappers import to_skill_assessment_dto
from src.backend.use_case.onboarding.diagnostic_questions import (
    evaluate_diagnostic_answers,
)


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
            study_timeline = StudyTimeline(payload.study_timeline)
        except ValueError as error:
            raise InvalidOnboardingDataError(
                "Некорректная цель, уровень или срок обучения"
            ) from error
        interests = self._parse_interests(payload.interests_text)
        if not interests:
            raise InvalidOnboardingDataError("Нужно указать хотя бы один интерес")
        try:
            skill_assessment = evaluate_diagnostic_answers(
                payload.diagnostic_answers,
                language_level,
                payload.diagnostic_hints_used,
            )
        except ValueError as error:
            raise InvalidOnboardingDataError(str(error)) from error

        await self._user_repository.update_learning_profile(
            user_id=user_id,
            goal=goal,
            language_level=language_level,
            study_timeline=study_timeline,
            interests=interests,
            skill_assessment=skill_assessment,
        )
        generated_batches: dict[str, int] = {}
        for track in TrackType:
            await self._generate_cards_use_case.execute(user_id, track)
            generated_batches[track.value] = 1
        return OnboardingResultDTO(
            user_id=user_id,
            generated_batches=generated_batches,
            skill_assessment=to_skill_assessment_dto(skill_assessment),
        )

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
