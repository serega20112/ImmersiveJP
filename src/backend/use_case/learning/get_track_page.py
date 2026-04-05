from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import TrackPageDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
    AbstractSessionRepository,
)
from src.backend.use_case.mappers import to_track_card_dto


class GetTrackPageUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
        session_repository: AbstractSessionRepository,
    ):
        self._content_repository = content_repository
        self._progress_repository = progress_repository
        self._session_repository = session_repository

    async def execute(self, user_id: int, track: TrackType) -> TrackPageDTO:
        session = await self._session_repository.get_track_session(user_id, track)
        current_batch = session.last_generated_batch if session is not None else 0
        cards = []
        if current_batch > 0:
            cards = await self._content_repository.list_cards_by_batch(
                user_id,
                track,
                current_batch,
            )
        card_ids = [int(card.id or 0) for card in cards]
        completed_ids = set(
            await self._progress_repository.list_completed_card_ids(user_id, card_ids)
        )
        completed_total = await self._progress_repository.get_completed_count(
            user_id, track
        )
        generated_total = await self._content_repository.count_cards(user_id, track)
        all_current_batch_completed = bool(cards) and all(
            int(card.id or 0) in completed_ids for card in cards
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
            can_generate_next=all_current_batch_completed,
        )
