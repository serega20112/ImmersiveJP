from __future__ import annotations

from abc import ABC
from typing import TypeVar

from sqlalchemy import func, select

from src.application.interfaces import PaginatedResult, ReadRepositoryPort

from .base_repo import BaseSQLAlchemyRepository

T = TypeVar("T")  # Domain entity
ID = TypeVar("ID")  # Entity ID type
F = TypeVar("F")  # Filters DTO
M = TypeVar("M")  # ORM model


class SQLAlchemyReadRepository(BaseSQLAlchemyRepository[T, ID, F, M], ReadRepositoryPort[T, ID, F], ABC):
    """
    Реализация Read-side репозитория для SQLAlchemy.

    Поддерживает:
        - get
        - find_one
        - find_all
        - paginate
        - exists
        - count

    Предназначен для использования с read-replica (опционально).
    """

    async def get(self, id: ID) -> T | None:
        """
        Получить сущность по ID.

        :param id: Идентификатор сущности
        :return: Сущность или None
        """
        model = await self._session.get(self.model, id)
        if model is None:
            return None

        return self.to_entity(model)

    async def find_one(self, filters: F) -> T | None:
        """
        Найти одну сущность по фильтрам.

        :param filters: Dataclass DTO
        """
        query = select(self.model)
        query = self._apply_filters(query, filters)
        query = self._apply_soft_delete_filter(query)

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        return self.to_entity(model) if model else None

    async def find_all(
        self,
        filters: F,
        *,
        skip: int = None,
        limit: int = None,
        order_by: str | None = None,
    ) -> list[T]:
        """
        Получить список сущностей.

        :param filters: DTO фильтров
        :param skip: Offset
        :param limit: Limit
        :param order_by: Поле сортировки (с '-' для DESC)
        """
        query = select(self.model)
        query = self._apply_filters(query, filters)
        query = self._apply_soft_delete_filter(query)

        if order_by:
            field_name = order_by.lstrip("-")
            column = getattr(self.model, field_name)
            query = query.order_by(column.desc()) if order_by.startswith("-") else query.order_by(column.asc())

        if skip is not None and limit is not None:
            query = query.offset(skip).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self.to_entity(m) for m in models]

    async def count(self, filters: F) -> int:
        """Подсчитать количество сущностей по фильтрам."""
        query = select(func.count()).select_from(self.model)
        query = self._apply_filters(query, filters)
        query = self._apply_soft_delete_filter(query)
        return await self._session.scalar(query) or 0

    async def exists(self, filters: F) -> bool:
        """Проверить существование хотя бы одной записи."""
        query = select(1).select_from(self.model).limit(1)
        query = self._apply_filters(query, filters)
        query = self._apply_soft_delete_filter(query)
        result = await self._session.execute(query)
        return result.first() is not None

    async def paginate(
        self,
        filters: F,
        *,
        page: int = 1,
        page_size: int = 20,
        order_by: str | None = None,
    ) -> PaginatedResult[T]:
        """
        Получить данные постранично.

        :param page: Номер страницы (с 1)
        :param page_size: Размер страницы
        """
        total = await self.count(filters)
        items = await self.find_all(filters, skip=(page - 1) * page_size, limit=page_size, order_by=order_by)
        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)
