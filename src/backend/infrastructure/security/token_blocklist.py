from __future__ import annotations

from hashlib import sha256

from src.backend.infrastructure.cache import KeyValueStore


class TokenBlocklist:
    def __init__(self, store: KeyValueStore):
        self._store = store

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        await self._store.set_json(self._key(token), {"revoked": True}, ttl_seconds)

    async def is_revoked(self, token: str) -> bool:
        return await self._store.get_json(self._key(token)) is not None

    @staticmethod
    def _key(token: str) -> str:
        return f"jwt:block:{sha256(token.encode('utf-8')).hexdigest()}"
