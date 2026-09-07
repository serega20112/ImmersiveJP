"""Порт отправки электронной почты."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Mailer(Protocol):
    """Порт отправки электронной почты."""

    async def send_verification_code(self, email: str, code: str) -> None:
        """Отправить письмо с кодом подтверждения."""
        pass
