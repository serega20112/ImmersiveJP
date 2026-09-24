"""Юнит-тесты реального PasswordService (pbkdf2_sha256)."""

import pytest

from src.infrastructures.security.password_service import PasswordService


class TestPasswordService:
    """Группа тестов хеширования и проверки паролей."""

    @pytest.fixture
    def service(self) -> PasswordService:
        """Реальный сервис паролей."""
        return PasswordService()

    async def test_hash_and_verify_roundtrip(self, service: PasswordService) -> None:
        """
        Тестируем: цикл хеширования и проверки.
        Отдаём: пароль "secret123".
        Ожидаем: verify возвращает True для исходного пароля и его хеша.
        """
        hashed = await service.hash_password("secret123")

        assert hashed != "secret123"
        assert await service.verify_password("secret123", hashed) is True

    async def test_verify_rejects_wrong_password(self, service: PasswordService) -> None:
        """
        Тестируем: проверку неверного пароля.
        Отдаём: хеш пароля "secret123" и пароль "wrong".
        Ожидаем: verify возвращает False.
        """
        hashed = await service.hash_password("secret123")

        assert await service.verify_password("wrong", hashed) is False

    async def test_hash_is_salted(self, service: PasswordService) -> None:
        """
        Тестируем: уникальность хешей одного пароля (соль).
        Отдаём: один и тот же пароль дважды.
        Ожидаем: хеши различаются.
        """
        first = await service.hash_password("same-password")
        second = await service.hash_password("same-password")

        assert first != second
