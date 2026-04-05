from __future__ import annotations

from src.backend.domain.content import LearningCard, TrackType
from src.backend.dto.learning_dto import TrackCardPageDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
    AbstractSessionRepository,
)
from src.backend.use_case.mappers import to_track_card_dto


class CardNotFoundError(Exception):
    pass


class GetCardPageUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
        session_repository: AbstractSessionRepository,
    ):
        self._content_repository = content_repository
        self._progress_repository = progress_repository
        self._session_repository = session_repository

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        card_id: int,
    ) -> TrackCardPageDTO:
        card = await self._content_repository.get_by_id(card_id)
        if card is None or card.user_id != user_id or card.track != track:
            raise CardNotFoundError("Карточка не найдена")

        batch_cards = await self._content_repository.list_cards_by_batch(
            user_id,
            track,
            card.batch_number,
        )
        batch_completed_ids = await self._get_completed_ids(user_id, batch_cards)

        session = await self._session_repository.get_track_session(user_id, track)
        current_batch = session.last_generated_batch if session is not None else 0
        completed_total = await self._progress_repository.get_completed_count(
            user_id, track
        )
        generated_total = await self._content_repository.count_cards(user_id, track)
        all_current_batch_completed = await self._is_current_batch_completed(
            user_id=user_id,
            track=track,
            current_batch=current_batch,
            card_batch=card.batch_number,
            batch_cards=batch_cards,
            batch_completed_ids=batch_completed_ids,
        )

        return TrackCardPageDTO(
            track=track.value,
            title=track.title,
            subtitle=track.subtitle,
            card=to_track_card_dto(card, batch_completed_ids),
            batch_cards=[
                to_track_card_dto(batch_card, batch_completed_ids)
                for batch_card in batch_cards
            ],
            current_batch=current_batch,
            completed_total=completed_total,
            generated_total=generated_total,
            all_current_batch_completed=all_current_batch_completed,
            can_generate_next=all_current_batch_completed,
        )

    async def _get_completed_ids(
        self,
        user_id: int,
        cards: list[LearningCard],
    ) -> set[int]:
        card_ids = [int(card.id or 0) for card in cards]
        return set(
            await self._progress_repository.list_completed_card_ids(user_id, card_ids)
        )

    async def _is_current_batch_completed(
        self,
        *,
        user_id: int,
        track: TrackType,
        current_batch: int,
        card_batch: int,
        batch_cards: list[LearningCard],
        batch_completed_ids: set[int],
    ) -> bool:
        if current_batch <= 0:
            return False
        if current_batch == card_batch:
            return bool(batch_cards) and all(
                int(card.id or 0) in batch_completed_ids for card in batch_cards
            )
        current_cards = await self._content_repository.list_cards_by_batch(
            user_id,
            track,
            current_batch,
        )
        current_completed_ids = await self._get_completed_ids(user_id, current_cards)
        return bool(current_cards) and all(
            int(card.id or 0) in current_completed_ids for card in current_cards
        )
