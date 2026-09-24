from __future__ import annotations

from src.application.dto.learning import TrackWorkPageDTO
from src.application.exceptions import TrackWorkUnavailableError
from src.application.interfaces import UnitOfWork
from src.application.use_cases.learning.work.grading import WORK_PASS_SCORE
from src.application.use_cases.learning.work.task_builder import build_prepared_work_tasks
from src.application.use_cases.mappers import to_track_work_task_dto
from src.domain.value_objects.track_type import TrackType


class GetTrackWorkPageUseCase:
    def __init__(self, uow: UnitOfWork):
        """Initialize the get track work page use case.

        Args:
            uow: Unit of work for database transactions.
        """
        self._uow = uow

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> TrackWorkPageDTO:
        """Get the track work page for a specific batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.

        Returns:
            The track work page data.

        Raises:
            TrackWorkUnavailableError: If the batch is not available for work.
        """
        async with self._uow as uow:
            content_repository = uow.repository("content")
            progress_repository = uow.repository("progress")
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
            review_cards = await self._load_review_cards(
                content_repository,
                progress_repository,
                user_id,
                track,
                batch_number,
            )
            tasks = build_prepared_work_tasks(track, cards, review_cards)
            return TrackWorkPageDTO(
                track=track.value,
                title=f"Работа по партии {batch_number}",
                subtitle="Партия уже закрыта. Теперь нужно показать, что материал реально используется без карточек перед глазами.",
                batch_number=batch_number,
                source_topics=[card.topic for card in cards[:5]],
                pass_score=WORK_PASS_SCORE,
                tasks=[to_track_work_task_dto(task) for task in tasks],
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
