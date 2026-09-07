from __future__ import annotations

from abc import ABC
from typing import Generic, TypeVar

from src.application.interfaces import RepositoryPort

from .read_repo import SQLAlchemyReadRepository
from .write_repo import SQLAlchemyWriteRepository

T = TypeVar("T")  # Domain entity
ID = TypeVar("ID")  # Entity ID type
F = TypeVar("F")  # Filters DTO
M = TypeVar("M")  # ORM model


class SQLAlchemyFullRepository(
    SQLAlchemyReadRepository[T, ID, F, M],
    SQLAlchemyWriteRepository[T, ID, F, M],
    RepositoryPort[T, ID, F],
    Generic[T, ID, F, M],
    ABC,
):
    """
    Полная реализация Repository-порта.

    Объединяет:
        - Read-side (запросы)
        - Write-side (команды)

    Используется, когда компоненту нужен полный доступ к данным.
    """

    pass
