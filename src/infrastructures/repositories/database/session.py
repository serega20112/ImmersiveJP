from __future__ import annotations

from sqlalchemy import select

from src.application.interfaces.database import LearningSessionRepositoryPort
from src.domain.entities import LearningSession
from src.domain.value_objects import BatchGenerationState, Timestamp, TrackType, UserID
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

    async def save_track_session(self, session: LearningSession) -> LearningSession:
        """Создать или обновить учебную сессию трека и вернуть доменную сущность.

        Сохраняются и номер партии, и состояние её генерации: для брони это одна
        атомарная операция, и разъезд этих значений оставил бы страницу следить
        за партией, которой статус не присвоен.

        После flush выполняется refresh всей строки: updated_at обновляется на
        стороне БД (onupdate=func.now()), и без явной догрузки в async-контексте
        обращение к атрибутам модели в to_entity спровоцирует ленивый SELECT вне
        greenlet (MissingGreenlet).
        """
        user_id = int(session.user_id)
        track_value = session.track.value
        started_at = (
            session.generation_started_at.value
            if session.generation_started_at is not None
            else None
        )
        result = await self._session.execute(
            select(LearningSessionModel).where(
                LearningSessionModel.user_id == user_id,
                LearningSessionModel.track == track_value,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            model = LearningSessionModel(
                user_id=user_id,
                track=track_value,
                last_generated_batch=session.last_generated_batch,
                generation_state=session.generation_state.value,
                generation_started_at=started_at,
            )
            self._session.add(model)
        else:
            model.last_generated_batch = session.last_generated_batch
            model.generation_state = session.generation_state.value
            model.generation_started_at = started_at
        await self._session.flush()
        await self._session.refresh(model)
        return self.to_entity(model)

    def to_entity(self, model: LearningSessionModel) -> LearningSession:
        """Преобразовать модель БД в доменную сущность.

        Args:
            model: Строка учебной сессии.

        Returns:
            Доменная сущность учебной сессии.
        """
        return LearningSession(
            user_id=UserID(model.user_id),
            track=TrackType(model.track),
            last_generated_batch=model.last_generated_batch,
            updated_at=Timestamp(model.updated_at),
            generation_state=BatchGenerationState(model.generation_state),
            generation_started_at=(
                Timestamp(model.generation_started_at)
                if model.generation_started_at is not None
                else None
            ),
        )
