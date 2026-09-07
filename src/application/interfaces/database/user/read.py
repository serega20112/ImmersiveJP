"""Порт чтения репозитория пользователей."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.interfaces.database.base.read import ReadRepositoryPort
from src.domain.aggregates.user import User


class UserReadRepositoryPort(ReadRepositoryPort[User, int, object], ABC):
    """Порт чтения агрегата User."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Найти пользователя по email."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        """Найти пользователя по идентификатору."""
        raise NotImplementedError
