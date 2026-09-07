"""Порт записи репозитория пользователей."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.interfaces.database.base.write import WriteRepositoryPort
from src.domain.aggregates.user import User


class UserWriteRepositoryPort(WriteRepositoryPort[User, int], ABC):
    """Порт записи агрегата User."""

    @abstractmethod
    async def add(self, user: User) -> User:
        """Сохранить нового пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def save(self, user: User) -> User:
        """Обновить существующего пользователя."""
        raise NotImplementedError
