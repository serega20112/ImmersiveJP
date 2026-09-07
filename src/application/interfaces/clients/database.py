"""Порт низкоуровневого клиента базы данных."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any


class DatabaseClient(ABC):
    """Порт низкоуровневого клиента базы данных."""

    @abstractmethod
    async def connect(self) -> None:
        """Установить соединение с базой данных."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Закрыть соединение с базой данных."""
        pass

    @abstractmethod
    async def execute(self, query: str, params: Mapping[str, Any] | None = None) -> Any:
        """Выполнить запрос без выборки результатов."""
        pass

    @abstractmethod
    async def fetch_one(
        self,
        query: str,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any] | None:
        """Выполнить запрос и вернуть первую строку."""
        pass

    @abstractmethod
    async def fetch_all(
        self,
        query: str,
        params: Mapping[str, Any] | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        """Выполнить запрос и вернуть все строки."""
        pass

    @abstractmethod
    def transaction(self) -> AbstractAsyncContextManager[Any]:
        """Открыть транзакцию."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Проверить доступность базы данных."""
        pass
