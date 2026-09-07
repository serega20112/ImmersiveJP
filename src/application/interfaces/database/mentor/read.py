"""Порт чтения репозитория наставника."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import MentorFocus, MentorMessage


class MentorReadRepositoryPort(ABC):
    """Порт чтения истории сообщений наставника."""

    @abstractmethod
    async def get_messages(self, user_id: int) -> list[MentorMessage]:
        """Получить историю сообщений пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def get_focus(self, user_id: int) -> MentorFocus | None:
        """Получить текущий фокус наставника."""
        raise NotImplementedError
