from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.content import LearningCard, TrackType
from src.backend.infrastructure.models import CardCompletionModel, LearningCardModel
from src.backend.infrastructure.repositories import AbstractContentRepository


class ContentRepository(AbstractContentRepository):
    def __init__(self, session: AsyncSession):
        """Initialize the content repository.

        Args:
            session: The async database session.
        """
        self._session = session

    async def add_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        """Add multiple learning cards to the database.

        Args:
            cards: The learning cards to add.

        Returns:
            The created learning card entities.
        """
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

    async def update_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        """Update multiple learning cards in the database.

        Args:
            cards: The learning cards with updated data.

        Returns:
            The updated learning card entities.
        """
        if not cards:
            return []
        card_map = {int(card.id or 0): card for card in cards if card.id is not None}
        result = await self._session.execute(
            select(LearningCardModel).where(LearningCardModel.id.in_(card_map.keys()))
        )
        models = result.scalars().all()
        for model in models:
            card = card_map.get(model.id)
            if card is None:
                continue
            model.topic = card.topic
            model.explanation = card.explanation
            model.examples_json = card.examples
            model.key_terms_json = card.key_terms
        await self._session.flush()
        await self._session.commit()
        ordered_models = sorted(models, key=lambda item: item.position)
        return [self._to_entity(model) for model in ordered_models]

    async def get_by_id(self, card_id: int) -> LearningCard | None:
        """Get a learning card by its ID.

        Args:
            card_id: ID of the card.

        Returns:
            The learning card entity, or None if not found.
        """
        result = await self._session.execute(
            select(LearningCardModel).where(LearningCardModel.id == card_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest_batch_number(self, user_id: int, track: TrackType) -> int:
        """Get the latest batch number for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The latest batch number, or 0 if none.
        """
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
        """List all cards in a specific batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.

        Returns:
            A list of learning card entities.
        """
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
        """List recent unique topics for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            limit: Maximum number of topics to return.

        Returns:
            A list of topic strings.
        """
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
        """Count total cards for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The total card count.
        """
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
        """List all completed cards for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            A list of completed learning card entities.
        """
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
        return [self._to_entity(model) for model in result.scalars().all()]

    async def list_card_ids_for_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[int]:
        """List card IDs for a specific batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.

        Returns:
            A list of card IDs.
        """
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
        """Convert a LearningCardModel to a LearningCard entity.

        Args:
            model: The database model.

        Returns:
            The learning card entity.
        """
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
