"""Порт чтения репозитория прогресса."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.value_objects.track_type import TrackType


class ProgressReadRepositoryPort(ABC):
    """Порт чтения прогресса по завершённым карточкам."""

    @abstractmethod
    async def list_completed_card_ids(
        self,
        user_id: int,
        card_ids: list[int],
    ) -> list[int]:
        """Получить идентификаторы завершённых карточек из перечисленных."""
        raise NotImplementedError

    @abstractmethod
    async def get_completed_count(self, user_id: int, track: TrackType) -> int:
        """Получить количество завершённых карточек по треку."""
        raise NotImplementedError

    @abstractmethod
    async def get_total_completed(self, user_id: int) -> int:
        """Получить общее количество завершённых карточек."""
        raise NotImplementedError

    @abstractmethod
    async def is_batch_completed(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> bool:
        """Проверить, завершён ли батч пользователем."""
        raise NotImplementedError
