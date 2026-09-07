"""Доменная модель результата постраничной выборки."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    """Результат пагинации, возвращаемый read-портом."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        """Количество страниц в выборке."""
        return (self.total + self.page_size - 1) // self.page_size
