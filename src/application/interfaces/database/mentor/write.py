"""Порт записи репозитория наставника."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import MentorFocus, MentorMessage


class MentorWriteRepositoryPort(ABC):
    """Порт записи истории сообщений наставника."""

    @abstractmethod
    async def save_messages(self, user_id: int, messages: list[MentorMessage]) -> None:
        """Сохранить историю сообщений пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def set_focus(self, user_id: int, focus: MentorFocus | None) -> None:
        """Сохранить текущий фокус наставника."""
        raise NotImplementedError
