from __future__ import annotations

from sqlalchemy import select

from src.application.interfaces.database import LearningSessionRepositoryPort
from src.domain.entities import LearningSession
from src.domain.value_objects import Timestamp, TrackType, UserID
from src.infrastructures.database.models import LearningSessionModel


class SessionRepository(LearningSessionRepositoryPort):
    """Репозиторий учебных сессий."""

    def __init__(self, session) -> None:
        self._session = session

    async def get_track_session(
        self,
        user_id: int,
        track: TrackType,
    ) -> LearningSession | None:
        result = await self._session.execute(
            select(LearningSessionModel).where(
                LearningSessionModel.user_id == user_id,
                LearningSessionModel.track == track.value,
            )
        )
        model = result.scalar_one_or_none()
        return self.to_entity(model) if model else None

    async def upsert_track_session(
        self,
        user_id: int,
        track: TrackType,
        last_generated_batch: int,
    ) -> LearningSession:
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
        await self._session.flush()
        return self.to_entity(model)

    def to_entity(self, model: LearningSessionModel) -> LearningSession:
        return LearningSession(
            user_id=UserID(model.user_id),
            track=TrackType(model.track),
            last_generated_batch=model.last_generated_batch,
            updated_at=Timestamp(model.updated_at),
        )
