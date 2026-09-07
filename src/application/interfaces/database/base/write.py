"""Порт репозитория записи (command-side в CQRS)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class WriteRepositoryPort(Generic[T, ID], ABC):
    """Порт для операций записи (command-side в CQRS)."""

    @abstractmethod
    async def create(self, entity: T) -> ID:
        """Создать сущность и вернуть её идентификатор."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> ID:
        """Обновить сущность и вернуть её идентификатор."""
        pass

    @abstractmethod
    async def delete(self, id: ID) -> bool:
        """Удалить сущность по идентификатору."""
        pass
