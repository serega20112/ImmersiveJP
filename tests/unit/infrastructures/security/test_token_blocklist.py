"""Юнит-тесты реального TokenBlocklist поверх memory-only KeyValueStore."""

import pytest

from src.infrastructures.cache import KeyValueStore
from src.infrastructures.security.token_blocklist import TokenBlocklist


@pytest.fixture
def blocklist() -> TokenBlocklist:
    """Блоклист токенов на in-memory хранилище."""
    return TokenBlocklist(KeyValueStore(redis_url=None, namespace="test-blocklist"))


class TestTokenBlocklist:
    """Группа тестов реестра отозванных токенов."""

    async def test_revoked_token_is_reported(self, blocklist: TokenBlocklist) -> None:
        """
        Тестируем: отзыв токена.
        Отдаём: токен с положительным TTL.
        Ожидаем: is_revoked True после revoke, False до него.
        """
        token = "token-a"

        assert await blocklist.is_revoked(token) is False
        await blocklist.revoke(token, ttl_seconds=60)
        assert await blocklist.is_revoked(token) is True

    async def test_revoke_ignores_non_positive_ttl(self, blocklist: TokenBlocklist) -> None:
        """
        Тестируем: отзыв с истёкшим TTL.
        Отдаём: токен с ttl_seconds=0.
        Ожидаем: revoke не выполняет запись, is_revoked остаётся False.
        """
        await blocklist.revoke("token-b", ttl_seconds=0)

        assert await blocklist.is_revoked("token-b") is False

    async def test_only_revoked_token_is_blocked(self, blocklist: TokenBlocklist) -> None:
        """
        Тестируем: изоляцию отзывов по токенам.
        Отдаём: отзыв одного из двух токенов.
        Ожидаем: второй токен не считается отозванным.
        """
        await blocklist.revoke("token-good", ttl_seconds=60)

        assert await blocklist.is_revoked("token-other") is False
