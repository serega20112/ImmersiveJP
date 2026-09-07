"""Порт хеширования и проверки паролей."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PasswordService(Protocol):
    """Порт хеширования и проверки паролей."""

    async def hash_password(self, password: str) -> str:
        """Вернуть хеш пароля."""
        pass

    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Проверить пароль против хеша."""
        pass
