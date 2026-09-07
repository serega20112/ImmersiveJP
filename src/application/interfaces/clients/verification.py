"""Порт хранилища кодов подтверждения email."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailVerificationStore(Protocol):
    """Порт хранилища кодов подтверждения email."""

    async def issue_code(self, email: str) -> str:
        """Выдать и сохранить новый код подтверждения."""
        pass

    async def verify_code(self, email: str, code: str) -> bool:
        """Проверить код подтверждения."""
        pass
