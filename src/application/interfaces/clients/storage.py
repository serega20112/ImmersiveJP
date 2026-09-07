"""Порт key-value хранилища (Redis или in-memory)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class KeyValueStore(Protocol):
    """Порт key-value хранилища (Redis или in-memory)."""

    async def get_json(self, key: str) -> Any:
        """Получить JSON-значение по ключу."""
        pass

    async def set_json(self, key: str, value: Any, expire_seconds: int | None = None) -> None:
        """Сохранить JSON-значение с опциональным TTL."""
        pass

    async def delete(self, key: str) -> None:
        """Удалить ключ."""
        pass

    async def incr(self, key: str, expire_seconds: int) -> int:
        """Инкрементировать счётчик и задать TTL."""
        pass

    async def close(self) -> None:
        """Закрыть соединение с хранилищем."""
        pass
