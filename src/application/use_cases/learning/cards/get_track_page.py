from __future__ import annotations

from src.application.dto.learning import TrackPageDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.batch_progress import summarize_completed_batches
from src.application.use_cases.mappers import to_track_card_dto
from src.domain.value_objects.track_type import TrackType


class GetTrackPageUseCase:
    def __init__(self, uow: UnitOfWork):
        """Initialize the get track page use case.

        Args:
            uow: Unit of work for database transactions.
        """
        self._uow = uow

    async def execute(self, user_id: int, track: TrackType) -> TrackPageDTO:
        """Get the track page for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The track page data.
        """
        async with self._uow as uow:
            content_repository = uow.repository("content")
            progress_repository = uow.repository("progress")
            session_repository = uow.repository("session")
            session = await session_repository.get_track_session(user_id, track)
            current_batch = session.last_generated_batch if session is not None else 0
            is_generating = session is not None and session.is_generating
            generation_failed = session is not None and session.needs_retry
            cards = []
            if current_batch > 0:
                cards = await content_repository.list_cards_by_batch(
                    user_id,
                    track,
                    current_batch,
                )
            card_ids = [int(card.id or 0) for card in cards]
            completed_ids = set(
                await progress_repository.list_completed_card_ids(user_id, card_ids)
            )
            completed_total = await progress_repository.get_completed_count(user_id, track)
            generated_total = await content_repository.count_cards(user_id, track)
            all_current_batch_completed = bool(cards) and all(
                int(card.id or 0) in completed_ids for card in cards
            )
            if is_generating:
                can_generate_next = False
            elif generation_failed:
                can_generate_next = True
            else:
                can_generate_next = not cards or all_current_batch_completed
            completed_batches, work_ready_batch = await summarize_completed_batches(
                progress_repository,
                user_id=user_id,
                track=track,
                current_batch=current_batch,
            )
            return TrackPageDTO(
                track=track.value,
                title=track.title,
                subtitle=track.subtitle,
                cards=[to_track_card_dto(card, completed_ids) for card in cards],
                current_batch=current_batch,
                completed_total=completed_total,
                generated_total=generated_total,
                all_current_batch_completed=all_current_batch_completed,
                can_generate_next=can_generate_next,
                generate_action_label=(
                    "Дописать партию"
                    if generation_failed
                    else ("Создать первую партию" if generated_total == 0 else "Следующая партия")
                ),
                completed_batches=completed_batches,
                work_ready_batch=work_ready_batch,
                is_generating=is_generating,
                generation_failed=generation_failed,
                work_href=(
                    f"/learn/{track.value}/work/{work_ready_batch}"
                    if work_ready_batch is not None
                    else None
                ),
            )
