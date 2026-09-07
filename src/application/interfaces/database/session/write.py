"""Порт записи репозитория учебных сессий."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import LearningSession
from src.domain.value_objects.track_type import TrackType


class LearningSessionWriteRepositoryPort(ABC):
    """Порт записи учебных сессий."""

    @abstractmethod
    async def upsert_track_session(
        self,
        user_id: int,
        track: TrackType,
        last_generated_batch: int,
    ) -> LearningSession:
        """Создать или обновить сессию пользователя по треку."""
        raise NotImplementedError
