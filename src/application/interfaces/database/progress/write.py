"""Порт записи репозитория прогресса."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProgressWriteRepositoryPort(ABC):
    """Порт записи прогресса по завершённым карточкам."""

    @abstractmethod
    async def complete_card(self, user_id: int, card_id: int) -> None:
        """Отметить карточку как завершённую."""
        raise NotImplementedError
