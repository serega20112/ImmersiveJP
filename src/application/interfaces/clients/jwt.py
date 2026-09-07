"""Порт выпуска и разбора JWT-токенов."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class JWTService(Protocol):
    """Порт выпуска и разбора JWT-токенов."""

    async def create_access_token(self, user_id: int) -> str:
        """Выпустить access-токен."""
        pass

    async def create_refresh_token(self, user_id: int) -> str:
        """Выпустить refresh-токен."""
        pass

    async def decode_access_token(self, token: str) -> int:
        """Разобрать access-токен и вернуть идентификатор пользователя."""
        pass

    async def decode_refresh_token(self, token: str) -> int:
        """Разобрать refresh-токен и вернуть идентификатор пользователя."""
        pass

    async def get_token_ttl_seconds(self, token: str) -> int:
        """Вернуть остаток времени жизни токена в секундах."""
        pass
