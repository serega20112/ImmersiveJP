from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.content import LearningCard, TrackType
from src.backend.infrastructure.models import CardCompletionModel, LearningCardModel
from src.backend.infrastructure.repositories import AbstractContentRepository


class ContentRepository(AbstractContentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        models = [
            LearningCardModel(
                user_id=card.user_id,
                track=card.track.value,
                topic=card.topic,
                explanation=card.explanation,
                examples_json=card.examples,
                key_terms_json=card.key_terms,
                batch_number=card.batch_number,
                position=card.position,
            )
            for card in cards
        ]
        self._session.add_all(models)
        await self._session.flush()
        await self._session.commit()
        return [self._to_entity(model) for model in models]

    async def get_by_id(self, card_id: int) -> LearningCard | None:
        result = await self._session.execute(
            select(LearningCardModel).where(LearningCardModel.id == card_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest_batch_number(self, user_id: int, track: TrackType) -> int:
        result = await self._session.execute(
            select(func.max(LearningCardModel.batch_number)).where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
        )
        return int(result.scalar() or 0)

    async def list_cards_by_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[LearningCard]:
        result = await self._session.execute(
            select(LearningCardModel)
            .where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
                LearningCardModel.batch_number == batch_number,
            )
            .order_by(LearningCardModel.position.asc())
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_recent_topics(
        self,
        user_id: int,
        track: TrackType,
        limit: int = 15,
    ) -> list[str]:
        result = await self._session.execute(
            select(LearningCardModel.topic)
            .where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
            .order_by(desc(LearningCardModel.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_cards(self, user_id: int, track: TrackType) -> int:
        result = await self._session.execute(
            select(func.count(LearningCardModel.id)).where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
        )
        return int(result.scalar() or 0)

    async def list_completed_cards(
        self,
        user_id: int,
        track: TrackType,
    ) -> list[LearningCard]:
        result = await self._session.execute(
            select(LearningCardModel)
            .join(
                CardCompletionModel, CardCompletionModel.card_id == LearningCardModel.id
            )
            .where(
                CardCompletionModel.user_id == user_id,
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
            .order_by(
                LearningCardModel.batch_number.asc(), LearningCardModel.position.asc()
            )
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_card_ids_for_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[int]:
        result = await self._session.execute(
            select(LearningCardModel.id).where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
                LearningCardModel.batch_number == batch_number,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    def _to_entity(model: LearningCardModel) -> LearningCard:
        return LearningCard(
            id=model.id,
            user_id=model.user_id,
            track=TrackType(model.track),
            topic=model.topic,
            explanation=model.explanation,
            examples=list(model.examples_json or []),
            key_terms=list(model.key_terms_json or []),
            batch_number=model.batch_number,
            position=model.position,
            created_at=model.created_at,
        )
