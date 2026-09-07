"""Порт репозитория чтения (query-side в CQRS)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from src.domain.entities.pagination import PaginatedResult

T = TypeVar("T")
ID = TypeVar("ID")
F = TypeVar("F")

OrderBy = str


class ReadRepositoryPort(Generic[T, ID, F], ABC):
    """Порт для операций чтения (query-side в CQRS)."""

    @abstractmethod
    async def get(self, id: ID) -> T | None:
        """Получить сущность по идентификатору."""
        pass

    @abstractmethod
    async def find_one(self, filters: F) -> T | None:
        """Найти одну сущность по фильтрам."""
        pass

    @abstractmethod
    async def find_all(
        self,
        filters: F,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: OrderBy | None = None,
    ) -> list[T]:
        """Найти список сущностей по фильтрам."""
        pass

    @abstractmethod
    async def paginate(
        self,
        filters: F,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: OrderBy | None = None,
    ) -> PaginatedResult[T]:
        """Постранично выбрать сущности по фильтрам."""
        pass

    @abstractmethod
    async def exists(self, filters: F) -> bool:
        """Проверить существование сущности по фильтрам."""
        pass

    @abstractmethod
    async def count(self, filters: F) -> int:
        """Посчитать количество сущностей по фильтрам."""
        pass
