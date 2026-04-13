from __future__ import annotations

import logging

from src.backend.dependencies.settings import Settings
from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import TrackWorkPageDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
    AbstractUserRepository,
)
from src.backend.use_case.learning.get_track_work_page import TrackWorkUnavailableError
from src.backend.use_case.learning.work_tasks import (
    build_prepared_work_tasks,
    evaluate_work_submission,
    to_track_work_task_dto,
    to_track_work_review_payload,
)

logger = get_logger(__name__)


class InvalidTrackWorkSubmissionError(Exception):
    pass


class SubmitTrackWorkUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
        llm_client: HuggingFaceLLMClient,
    ):
        self._user_repository = user_repository
        self._content_repository = content_repository
        self._progress_repository = progress_repository
        self._llm_client = llm_client

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        answers: dict[str, str],
    ) -> TrackWorkPageDTO:
        self._validate_answers(answers)
        cards = await self._content_repository.list_cards_by_batch(
            user_id,
            track,
            batch_number,
        )
        if not cards:
            raise TrackWorkUnavailableError("Партия для работы не найдена")
        if not await self._progress_repository.is_batch_completed(
            user_id,
            track,
            batch_number,
        ):
            raise TrackWorkUnavailableError(
                "Работа открывается только после полного завершения партии"
            )
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        review_cards = await self._load_review_cards(user_id, track, batch_number)
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
        for value in answers.values():
            if len(str(value).strip()) > Settings.text_input_limit:
                raise InvalidTrackWorkSubmissionError(
                    f"Один из ответов длиннее {Settings.text_input_limit} символов"
                )

    async def _load_review_cards(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list:
        if batch_number <= 1:
            return []
        previous_batch = batch_number - 1
        if not await self._progress_repository.is_batch_completed(
            user_id,
            track,
            previous_batch,
        ):
            return []
        return await self._content_repository.list_cards_by_batch(
            user_id,
            track,
            previous_batch,
        )
