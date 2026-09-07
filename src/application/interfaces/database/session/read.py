"""Порт чтения репозитория учебных сессий."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import LearningSession
from src.domain.value_objects.track_type import TrackType


class LearningSessionReadRepositoryPort(ABC):
    """Порт чтения учебных сессий."""

    @abstractmethod
    async def get_track_session(
        self,
        user_id: int,
        track: TrackType,
    ) -> LearningSession | None:
        """Получить сессию пользователя по треку."""
        raise NotImplementedError
