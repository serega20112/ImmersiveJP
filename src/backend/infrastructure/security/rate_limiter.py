from __future__ import annotations

from src.backend.infrastructure.cache import KeyValueStore


class RateLimiter:
    def __init__(self, store: KeyValueStore):
        self._store = store

    async def is_allowed(
        self,
        scope: str,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        counter = await self._store.incr(
            f"rate-limit:{scope}:{key}",
            expire_seconds=window_seconds,
        )
        return counter <= limit
