from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.content import TrackType
from src.backend.infrastructure.models import CardCompletionModel, LearningCardModel
from src.backend.infrastructure.repositories import AbstractProgressRepository


class ProgressRepository(AbstractProgressRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def complete_card(self, user_id: int, card_id: int) -> None:
        existing = await self._session.execute(
            select(CardCompletionModel).where(
                CardCompletionModel.user_id == user_id,
                CardCompletionModel.card_id == card_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return
        completion = CardCompletionModel(user_id=user_id, card_id=card_id)
        self._session.add(completion)
        await self._session.commit()

    async def list_completed_card_ids(
        self, user_id: int, card_ids: list[int]
    ) -> list[int]:
        if not card_ids:
            return []
        result = await self._session.execute(
            select(CardCompletionModel.card_id).where(
                CardCompletionModel.user_id == user_id,
                CardCompletionModel.card_id.in_(card_ids),
            )
        )
        return list(result.scalars().all())

    async def get_completed_count(self, user_id: int, track: TrackType) -> int:
        result = await self._session.execute(
            select(func.count(CardCompletionModel.id))
            .join(
                LearningCardModel, LearningCardModel.id == CardCompletionModel.card_id
            )
            .where(
                CardCompletionModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
        )
        return int(result.scalar() or 0)

    async def get_total_completed(self, user_id: int) -> int:
        result = await self._session.execute(
            select(func.count(CardCompletionModel.id)).where(
                CardCompletionModel.user_id == user_id,
            )
        )
        return int(result.scalar() or 0)

    async def is_batch_completed(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> bool:
        total_result = await self._session.execute(
            select(func.count(LearningCardModel.id)).where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
                LearningCardModel.batch_number == batch_number,
            )
        )
        total_cards = int(total_result.scalar() or 0)
        if total_cards == 0:
            return False
        completed_result = await self._session.execute(
            select(func.count(CardCompletionModel.id))
            .join(
                LearningCardModel, LearningCardModel.id == CardCompletionModel.card_id
            )
            .where(
                CardCompletionModel.user_id == user_id,
                LearningCardModel.track == track.value,
                LearningCardModel.batch_number == batch_number,
            )
        )
        completed_cards = int(completed_result.scalar() or 0)
        return completed_cards >= total_cards
