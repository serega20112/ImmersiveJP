"""Юнит-тесты реального EmailVerificationStore поверх memory-only KeyValueStore."""

import pytest

from src.infrastructures.cache import KeyValueStore
from src.infrastructures.security.email_verification_store import EmailVerificationStore


@pytest.fixture
def store() -> EmailVerificationStore:
    """Хранилище кодов подтверждения на in-memory кеше."""
    return EmailVerificationStore(KeyValueStore(redis_url=None, namespace="test-verify"), ttl_seconds=120)


class TestEmailVerificationStore:
    """Группа тестов выпуска и проверки кодов подтверждения."""

    async def test_issue_returns_six_digit_code(self, store: EmailVerificationStore) -> None:
        """
        Тестируем: выпуск кода.
        Отдаём: адрес электронной почты.
        Ожидаем: шестизначный числовой код.
        """
        code = await store.issue_code("user@example.com")

        assert len(code) == 6
        assert code.isdigit()

    async def test_verify_accepts_issued_code_once(self, store: EmailVerificationStore) -> None:
        """
        Тестируем: одноразовость кода.
        Отдаём: выпущенный код; затем повторная проверка.
        Ожидаем: первая проверка True, вторая False (код погашен).
        """
        code = await store.issue_code("user@example.com")

        assert await store.verify_code("user@example.com", code) is True
        assert await store.verify_code("user@example.com", code) is False

    async def test_verify_rejects_wrong_code(self, store: EmailVerificationStore) -> None:
        """
        Тестируем: проверку неверного кода.
        Отдаём: выпущенный код и другую комбинацию.
        Ожидаем: False, код в хранилище не гасится.
        """
        await store.issue_code("user@example.com")

        assert await store.verify_code("user@example.com", "000000") is False

    async def test_verify_without_issue_returns_false(self, store: EmailVerificationStore) -> None:
        """
        Тестируем: проверку кода без предварительного выпуска.
        Отдаём: адрес без выпущенного кода.
        Ожидаем: False.
        """
        assert await store.verify_code("ghost@example.com", "123456") is False
