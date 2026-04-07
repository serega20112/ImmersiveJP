from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import TrackWorkPageDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
)
from src.backend.use_case.learning.get_track_work_page import TrackWorkUnavailableError
from src.backend.use_case.learning.work_tasks import (
    build_prepared_work_tasks,
    evaluate_work_submission,
    to_track_work_task_dto,
)


class SubmitTrackWorkUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
    ):
        self._content_repository = content_repository
        self._progress_repository = progress_repository

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        answers: dict[str, str],
    ) -> TrackWorkPageDTO:
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
        review_cards = await self._load_review_cards(user_id, track, batch_number)
        tasks = build_prepared_work_tasks(track, cards, review_cards)
        result = evaluate_work_submission(tasks, answers, track=track)
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
