"""Порт хранилища отозванных токенов."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TokenBlocklist(Protocol):
    """Порт хранилища отозванных токенов."""

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Отозвать токен на время оставшейся жизни."""
        pass

    async def is_revoked(self, token: str) -> bool:
        """Проверить, отозван ли токен."""
        pass
