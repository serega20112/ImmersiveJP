from __future__ import annotations

import logging

from src.application.dto.onboarding import OnboardingDTO, OnboardingResultDTO
from src.application.exceptions import InvalidOnboardingDataError
from src.application.interfaces import UnitOfWork
from src.application.use_cases.learning.cards.generate_cards import GenerateCardsUseCase
from src.application.use_cases.mappers import to_skill_assessment_dto
from src.application.use_cases.onboarding.diagnostic_questions import (
    evaluate_diagnostic_answers,
)
from src.config.settings import settings
from src.domain.exceptions import UserNotOnboardedError
from src.domain.value_objects.track_type import TrackType
from src.domain.value_objects.user import LanguageLevel, LearningGoal, StudyTimeline
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class CompleteOnboardingUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        generate_cards_use_case: GenerateCardsUseCase,
    ):
        """Initialize the complete onboarding use case.

        Args:
            uow: Unit of work for database transactions.
            generate_cards_use_case: Use case for generating learning cards.
        """
        self._uow = uow
        self._generate_cards_use_case = generate_cards_use_case

    async def execute(self, user_id: int, payload: OnboardingDTO) -> OnboardingResultDTO:
        """Complete the onboarding process for a user.

        Args:
            user_id: ID of the user.
            payload: The onboarding form data.

        Returns:
            The onboarding result data.

        Raises:
            InvalidOnboardingDataError: If onboarding data is invalid.
        """
        try:
            goal = LearningGoal(payload.goal)
            language_level = LanguageLevel(payload.language_level)
            study_timeline = StudyTimeline(payload.study_timeline)
        except ValueError as error:
            raise InvalidOnboardingDataError(
                "Некорректная цель, уровень или срок обучения"
            ) from error
        if len(payload.interests_text.strip()) > settings.app.text_input_limit:
            raise InvalidOnboardingDataError(
                f"Поле интересов ограничено {settings.app.text_input_limit} символами"
            )
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

        async with self._uow as uow:
            user_repository = uow.repository("user")
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise InvalidOnboardingDataError("Пользователь не найден")
            try:
                user.complete_onboarding(
                    goal=goal,
                    level=language_level,
                    timeline=study_timeline,
                    interests=interests,
                    assessment=skill_assessment,
                )
            except UserNotOnboardedError as error:
                raise InvalidOnboardingDataError(str(error)) from error
            await user_repository.save(user)
        generated_batches: dict[str, int] = {}
        await self._generate_cards_use_case.execute(user_id, TrackType.LANGUAGE)
        generated_batches[TrackType.LANGUAGE.value] = 1
        log_event(
            logger,
            logging.INFO,
            "onboarding.completed",
            "User completed onboarding",
            user_id=user_id,
            goal=goal.value,
            language_level=language_level.value,
            study_timeline=study_timeline.value,
            interests_count=len(interests),
            generated_tracks=list(generated_batches.keys()),
        )
        return OnboardingResultDTO(
            user_id=user_id,
            generated_batches=generated_batches,
            skill_assessment=to_skill_assessment_dto(skill_assessment),
        )

    @staticmethod
    def _parse_interests(raw_value: str) -> list[str]:
        """Parse a raw interests string into a deduplicated list.

        Args:
            raw_value: Raw comma or newline separated interests.

        Returns:
            A list of unique interest strings.
        """
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
