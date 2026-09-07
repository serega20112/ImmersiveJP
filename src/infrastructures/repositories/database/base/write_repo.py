from __future__ import annotations

import uuid
from abc import ABC
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy.exc import IntegrityError

from src.application.interfaces import WriteRepositoryPort
from src.application.interfaces.exceptions import DatabaseError
from src.utils import value_or_none

from .base_repo import BaseSQLAlchemyRepository

T = TypeVar("T")  # Domain entity
ID = TypeVar("ID")  # Entity ID type
F = TypeVar("F")  # Filters DTO
M = TypeVar("M")  # ORM model


class SQLAlchemyWriteRepository(BaseSQLAlchemyRepository[T, ID, F, M], WriteRepositoryPort[T, ID], ABC):
    """
    Реализация Write-side репозитория.

    Предназначен для работы с primary БД.
    """

    async def create(self, entity: T) -> ID:
        """
        Создать новую сущность.

        :return: ID созданной сущности
        """
        model = self.to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def update(self, entity: T) -> ID:
        """
        Обновить существующую сущность.

        Использует optimistic locking (если поле версии присутствует).
        """
        pk = value_or_none(entity.id)
        if isinstance(pk, str):
            try:
                pk = uuid.UUID(pk)
            except ValueError:
                raise DatabaseError("Неправильный тип ID записи")
        elif not isinstance(pk, (int, uuid.UUID)):
            raise DatabaseError("Неправильный тип ID записи")

        instance = await self._session.get(self.model, pk)

        if instance is None:
            raise DatabaseError("Запись в базе не найдена")

        if hasattr(instance, self.soft_delete_field) and getattr(instance, self.soft_delete_field) is not None:
            raise DatabaseError("Нельзя обновлять удаленную(soft deleted) запись")

        await self._apply_optimistic_lock(instance, entity)

        updated_model = self.to_model(entity)

        for attr in vars(updated_model):
            if attr.startswith("_"):
                continue
            setattr(instance, attr, getattr(updated_model, attr))

        await self._session.flush()
        return instance.id

    async def delete(self, id: ID) -> bool:
        """
        Удалить сущность.

        Если поддерживается soft-delete → выставляется флаг.
        Иначе выполняется физическое удаление.
        """
        instance = await self._session.get(self.model, id)
        if instance is None:
            return False

        if hasattr(instance, self.soft_delete_field):
            if getattr(instance, self.soft_delete_field) is not None:
                return False

            setattr(instance, self.soft_delete_field, datetime.now(UTC))

        else:
            await self._session.delete(instance)

        try:
            await self._session.flush()
        except IntegrityError:
            raise DatabaseError("Удаление невозможно: запись имеет связанные данные в системе")
        return True
