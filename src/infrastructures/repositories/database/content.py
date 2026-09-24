from __future__ import annotations

from sqlalchemy import desc, func, select

from src.application.interfaces.database import LearningCardRepositoryPort
from src.domain.entities import LearningCard
from src.domain.value_objects import (
    BatchNumber,
    CardPosition,
    LearningCardID,
    Timestamp,
    TrackType,
    UserID,
)
from src.infrastructures.database.models import CardCompletionModel, LearningCardModel
from src.infrastructures.repositories.database.base import SQLAlchemyFullRepository
from src.utils import value_or_none


class LearningCardRepository(
    LearningCardRepositoryPort,
    SQLAlchemyFullRepository[LearningCard, LearningCardID, object, LearningCardModel],
):
    """Репозиторий учебных карточек."""

    model = LearningCardModel

    async def get_by_id(self, card_id: int) -> LearningCard | None:
        result = await self._session.execute(
            select(LearningCardModel).where(LearningCardModel.id == card_id)
        )
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

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
        return [self.to_entity(model) for model in result.scalars().all()]

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

    async def list_recent_key_terms(
        self,
        user_id: int,
        track: TrackType,
        limit: int = 40,
    ) -> list[str]:
        """Вернуть ключевые термины последних карточек без повторов (по created_at desc)."""
        result = await self._session.execute(
            select(LearningCardModel.key_terms_json)
            .where(
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
            .order_by(desc(LearningCardModel.created_at))
            .limit(limit)
        )
        terms: list[str] = []
        seen: set[str] = set()
        for row in result.scalars().all():
            for term in row or []:
                normalized = str(term).strip()
                marker = normalized.casefold()
                if not normalized or marker in seen:
                    continue
                seen.add(marker)
                terms.append(normalized)
        return terms

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
            .join(CardCompletionModel, CardCompletionModel.card_id == LearningCardModel.id)
            .where(
                CardCompletionModel.user_id == user_id,
                LearningCardModel.user_id == user_id,
                LearningCardModel.track == track.value,
            )
            .order_by(LearningCardModel.batch_number.asc(), LearningCardModel.position.asc())
        )
        return [self.to_entity(model) for model in result.scalars().all()]

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

    def to_entity(self, model: LearningCardModel) -> LearningCard:
        return LearningCard(
            id=LearningCardID(model.id),
            user_id=UserID(model.user_id),
            track=TrackType(model.track),
            topic=model.topic,
            explanation=model.explanation,
            examples=list(model.examples_json or []),
            key_terms=list(model.key_terms_json or []),
            batch_number=BatchNumber(model.batch_number),
            position=CardPosition(model.position),
            created_at=Timestamp(model.created_at),
        )

    def to_model(self, entity: LearningCard) -> LearningCardModel:
        return LearningCardModel(
            id=value_or_none(entity.id),
            user_id=int(entity.user_id),
            track=entity.track.value,
            topic=entity.topic,
            explanation=entity.explanation,
            examples_json=entity.examples,
            key_terms_json=entity.key_terms,
            batch_number=int(entity.batch_number),
            position=int(entity.position),
            created_at=value_or_none(entity.created_at),
        )
