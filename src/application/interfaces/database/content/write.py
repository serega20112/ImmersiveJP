"""Порт записи репозитория учебных карточек."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.interfaces.database.base.write import WriteRepositoryPort
from src.domain.entities import LearningCard


class LearningCardWriteRepositoryPort(WriteRepositoryPort[LearningCard, int], ABC):
    """Порт записи учебных карточек."""

    @abstractmethod
    async def add_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        """Сохранить список новых карточек."""
        raise NotImplementedError

    @abstractmethod
    async def update_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        """Обновить список существующих карточек."""
        raise NotImplementedError
