from __future__ import annotations

import secrets

from src.backend.infrastructure.cache import KeyValueStore


class EmailVerificationStore:
    def __init__(self, store: KeyValueStore, ttl_seconds: int):
        self._store = store
        self._ttl_seconds = ttl_seconds

    async def issue_code(self, email: str) -> str:
        code = str(secrets.randbelow(900000) + 100000)
        await self._store.set_json(
            self._key(email),
            {"code": code},
            expire_seconds=self._ttl_seconds,
        )
        return code

    async def verify_code(self, email: str, code: str) -> bool:
        stored = await self._store.get_json(self._key(email))
        if stored is None or stored.get("code") != code:
            return False
        await self._store.delete(self._key(email))
        return True

    @staticmethod
    def _key(email: str) -> str:
        return f"verify-email:{email}"
