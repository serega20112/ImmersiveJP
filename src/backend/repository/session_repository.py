from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.domain.content import TrackType
from src.backend.domain.session import LearningSession
from src.backend.infrastructure.models import LearningSessionModel
from src.backend.infrastructure.repositories import AbstractSessionRepository


class SessionRepository(AbstractSessionRepository):
    def __init__(self, session: AsyncSession):
        """Initialize the session repository.

        Args:
            session: The async database session.
        """
        self._session = session

    async def get_track_session(
        self,
        user_id: int,
        track: TrackType,
    ) -> LearningSession | None:
        """Get the current learning session for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The learning session, or None if not found.
        """
        result = await self._session.execute(
            select(LearningSessionModel).where(
                LearningSessionModel.user_id == user_id,
                LearningSessionModel.track == track.value,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def upsert_track_session(
        self,
        user_id: int,
        track: TrackType,
        last_generated_batch: int,
    ) -> LearningSession:
        """Create or update a learning session for a user and track.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            last_generated_batch: The latest generated batch number.

        Returns:
            The learning session entity.
        """
        result = await self._session.execute(
            select(LearningSessionModel).where(
                LearningSessionModel.user_id == user_id,
                LearningSessionModel.track == track.value,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = LearningSessionModel(
                user_id=user_id,
                track=track.value,
                last_generated_batch=last_generated_batch,
            )
            self._session.add(model)
        else:
            model.last_generated_batch = last_generated_batch
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: LearningSessionModel) -> LearningSession:
        """Convert a LearningSessionModel to a LearningSession entity.

        Args:
            model: The database model.

        Returns:
            The learning session entity.
        """
        return LearningSession(
            id=model.id,
            user_id=model.user_id,
            track=TrackType(model.track),
            last_generated_batch=model.last_generated_batch,
            updated_at=model.updated_at,
        )
