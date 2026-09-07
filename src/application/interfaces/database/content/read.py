"""Порт чтения репозитория учебных карточек."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.interfaces.database.base.read import ReadRepositoryPort
from src.domain.entities import LearningCard
from src.domain.value_objects.track_type import TrackType


class LearningCardReadRepositoryPort(ReadRepositoryPort[LearningCard, int, object], ABC):
    """Порт чтения учебных карточек."""

    @abstractmethod
    async def get_by_id(self, card_id: int) -> LearningCard | None:
        """Получить карточку по идентификатору."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest_batch_number(self, user_id: int, track: TrackType) -> int:
        """Получить номер последнего батча пользователя по треку."""
        raise NotImplementedError

    @abstractmethod
    async def list_cards_by_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[LearningCard]:
        """Получить карточки конкретного батча."""
        raise NotImplementedError

    @abstractmethod
    async def list_recent_topics(
        self,
        user_id: int,
        track: TrackType,
        limit: int = 15,
    ) -> list[str]:
        """Получить темы последних карточек."""
        raise NotImplementedError

    @abstractmethod
    async def count_cards(self, user_id: int, track: TrackType) -> int:
        """Посчитать количество карточек пользователя по треку."""
        raise NotImplementedError

    @abstractmethod
    async def list_completed_cards(
        self,
        user_id: int,
        track: TrackType,
    ) -> list[LearningCard]:
        """Получить завершённые карточки пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def list_card_ids_for_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[int]:
        """Получить идентификаторы карточек конкретного батча."""
        raise NotImplementedError
