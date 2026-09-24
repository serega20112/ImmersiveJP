from __future__ import annotations

import logging

from src.application.dto.learning import TrackWorkPageDTO
from src.application.exceptions import (
    InvalidTrackWorkSubmissionError,
    TrackWorkUnavailableError,
)
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient
from src.application.use_cases.learning.work.grading import evaluate_work_submission
from src.application.use_cases.learning.work.task_builder import build_prepared_work_tasks
from src.application.use_cases.mappers import (
    to_track_work_review_payload,
    to_track_work_task_dto,
)
from src.config.settings import settings
from src.domain.value_objects.track_type import TrackType
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class SubmitTrackWorkUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        llm_client: LLMClient,
    ):
        """Initialize the submit track work use case.

        Args:
            uow: Unit of work for database transactions.
            llm_client: Client for LLM work review.
        """
        self._uow = uow
        self._llm_client = llm_client

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        answers: dict[str, str],
    ) -> TrackWorkPageDTO:
        """Submit answers for a track work batch and get results.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.
            answers: Dictionary of task ID to answer text.

        Returns:
            The track work page with results.

        Raises:
            InvalidTrackWorkSubmissionError: If answers are invalid.
            TrackWorkUnavailableError: If the batch is not available for work.
        """
        self._validate_answers(answers)
        async with self._uow as uow:
            user_repository = uow.users
            content_repository = uow.learning_cards
            progress_repository = uow.progress
            cards = await content_repository.list_cards_by_batch(
                user_id,
                track,
                batch_number,
            )
            if not cards:
                raise TrackWorkUnavailableError("Партия для работы не найдена")
            if not await progress_repository.is_batch_completed(
                user_id,
                track,
                batch_number,
            ):
                raise TrackWorkUnavailableError(
                    "Работа открывается только после полного завершения партии"
                )
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")
            review_cards = await self._load_review_cards(
                content_repository,
                progress_repository,
                user_id,
                track,
                batch_number,
            )
        tasks = build_prepared_work_tasks(track, cards, review_cards)
        fallback_result = evaluate_work_submission(tasks, answers, track=track)
        result = await self._llm_client.review_track_work(
            user=user,
            track=track,
            batch_number=batch_number,
            tasks=[
                to_track_work_review_payload(task, submitted_answer=answers.get(task.id))
                for task in tasks
            ],
            fallback_result=fallback_result,
        )
        log_event(
            logger,
            logging.INFO,
            "learning.work_submitted",
            "Submitted track work",
            user_id=user_id,
            track=track.value,
            batch_number=batch_number,
            score=result.score,
            passed=result.passed,
        )
        return TrackWorkPageDTO(
            track=track.value,
            title=f"Работа по партии {batch_number}",
            subtitle="Оценка строится только на материале уже завершенной партии.",
            batch_number=batch_number,
            source_topics=[card.topic for card in cards[:5]],
            pass_score=result.pass_score,
            tasks=[
                to_track_work_task_dto(task, submitted_answer=answers.get(task.id))
                for task in tasks
            ],
            result=result,
        )

    @staticmethod
    def _validate_answers(answers: dict[str, str]) -> None:
        """Validate that all answers are within the text length limit.

        Args:
            answers: Dictionary of task ID to answer text.

        Raises:
            InvalidTrackWorkSubmissionError: If any answer exceeds the limit.
        """
        for value in answers.values():
            if len(str(value).strip()) > settings.app.text_input_limit:
                raise InvalidTrackWorkSubmissionError(
                    f"Один из ответов длиннее {settings.app.text_input_limit} символов"
                )

    async def _load_review_cards(
        self,
        content_repository,
        progress_repository,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list:
        """Load review cards from the previous batch if completed.

        Args:
            content_repository: Repository for content data.
            progress_repository: Repository for progress data.
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The current batch number.

        Returns:
            A list of review cards from the previous batch.
        """
        if batch_number <= 1:
            return []
        previous_batch = batch_number - 1
        if not await progress_repository.is_batch_completed(
            user_id,
            track,
            previous_batch,
        ):
            return []
        return await content_repository.list_cards_by_batch(
            user_id,
            track,
            previous_batch,
        )
