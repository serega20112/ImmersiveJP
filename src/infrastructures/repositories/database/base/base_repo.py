from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from typing import Generic, TypeVar

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.application.interfaces.exceptions import DatabaseError

T = TypeVar("T")  # Domain entity
ID = TypeVar("ID")  # Entity ID type
F = TypeVar("F")  # Filters DTO
M = TypeVar("M")  # ORM model


class BaseSQLAlchemyRepository(Generic[T, ID, F, M], ABC):
    """
    Базовый инфраструктурный класс для SQLAlchemy-репозиториев.

    Содержит:
        - Общую логику фильтрации (dataclass introspection)
        - Soft delete поддержку
        - Optimistic locking поддержку
        - Вспомогательные методы для наследников

    Этот класс НЕ реализует интерфейсы портов напрямую.
    Реализация разделена на Read и Write репозитории (CQRS).
    """

    #: ORM модель (обязательно переопределяется в наследнике)
    model: type[M]

    #: Название поля soft-delete (если используется)
    soft_delete_field: str = "deleted_at"

    #: Название поля версии для optimistic locking
    version_field: str = "version"

    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    # ========================
    # ===== Mapping API ======
    # ========================

    @abstractmethod
    def to_entity(self, model: M) -> T:
        """Преобразовать ORM-модель в доменную сущность."""
        raise NotImplementedError

    @abstractmethod
    def to_model(self, entity: T) -> M:
        """Преобразовать доменную сущность в ORM-модель."""
        raise NotImplementedError

    # ==========================
    # ===== Filter Builder =====
    # ==========================

    def _apply_filters(self, query: Select, filters: F | None) -> Select:
        """
        Применяет фильтры к SQLAlchemy-запросу через dataclass introspection.

        Логика:
            - Если filters = None → запрос без изменений
            - Игнорируются поля со значением None
            - Поле должно существовать в ORM-модели
            - Строки с '%' трактуются как ilike

        :param query: SQLAlchemy Select
        :param filters: Dataclass DTO с фильтрами
        :return: Обновлённый Select
        """
        if filters is None:
            return query

        if not is_dataclass(filters):
            raise DatabaseError("Под параметром filters должен передаваться dataclass")

        conditions = []

        for field in fields(filters):
            value = getattr(filters, field.name)
            if value is None or not hasattr(self.model, field.name):
                continue

            column = getattr(self.model, field.name)
            if isinstance(value, str) and "%" in value:
                conditions.append(column.ilike(value))
            else:
                conditions.append(column == value)

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _apply_soft_delete_filter(self, query: Select) -> Select:
        """
        Добавляет фильтр soft-delete, если модель поддерживает его.

        Модель базы должна содержать поле мягкого удаления (имя объявляется в переменной `soft_delete_field`).
        """
        if hasattr(self.model, self.soft_delete_field):
            column = getattr(self.model, self.soft_delete_field)
            query = query.where(column.is_(None))

        return query

    async def _apply_optimistic_lock(self, model: M, entity: T) -> None:
        """
        Проверяет optimistic locking.

        Если версия не совпадает → возбуждает исключение.
        """
        if not hasattr(model, self.version_field):
            return

        current_version = getattr(model, self.version_field)
        entity_version = getattr(entity, self.version_field, None)

        if current_version != entity_version:
            raise DatabaseError("Обнаружен конфликт версий записи")

        setattr(model, self.version_field, current_version + 1)
