"""Комбинированный порт репозитория (чтение + запись)."""

from __future__ import annotations

from abc import ABC
from typing import Generic, TypeVar

from src.application.interfaces.database.base.read import ReadRepositoryPort
from src.application.interfaces.database.base.write import WriteRepositoryPort

T = TypeVar("T")
ID = TypeVar("ID")
F = TypeVar("F")


class RepositoryPort(ReadRepositoryPort[T, ID, F], WriteRepositoryPort[T, ID], Generic[T, ID, F], ABC):
    """Комбинированный порт репозитория (чтение + запись)."""
