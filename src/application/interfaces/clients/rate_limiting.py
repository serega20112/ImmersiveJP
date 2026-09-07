"""Порт ограничителя частоты запросов."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class RateLimiter(Protocol):
    """Порт ограничителя частоты запросов."""

    async def consume(self, scope: str, key: str, window_seconds: int) -> int:
        """Увеличить счётчик в окне и вернуть текущее значение."""
        pass

    async def is_allowed(self, scope: str, key: str, limit: int, window_seconds: int) -> bool:
        """Проверить, не превышен ли лимит запросов."""
        pass
