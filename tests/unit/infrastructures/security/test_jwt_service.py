"""Юнит-тесты реального JWTService: выпуск, разбор, типы и TTL токенов."""

import jwt as pyjwt
import pytest

from src.config.settings import settings
from src.infrastructures.security.jwt_service import JWTService


class TestJWTService:
    """Группа тестов выпуска и разбора JWT."""

    @pytest.fixture
    def service(self) -> JWTService:
        """Реальный JWTService на секретах из настроек."""
        return JWTService()

    async def test_access_token_roundtrip(self, service: JWTService) -> None:
        """
        Тестируем: выпуск и разбор access-токена.
        Отдаём: идентификатор пользователя 42.
        Ожидаем: decode_access_token возвращает 42.
        """
        token = await service.create_access_token(42)

        assert await service.decode_access_token(token) == 42

    async def test_refresh_token_roundtrip(self, service: JWTService) -> None:
        """
        Тестируем: выпуск и разбор refresh-токена.
        Отдаём: идентификатор пользователя 7.
        Ожидаем: decode_refresh_token возвращает 7.
        """
        token = await service.create_refresh_token(7)

        assert await service.decode_refresh_token(token) == 7

    async def test_rejects_refresh_token_as_access(self, service: JWTService) -> None:
        """
        Тестируем: подмену типа токена.
        Отдаём: refresh-токен в decode_access_token.
        Ожидаем: выброс jwt.InvalidTokenError (тип не совпал).
        """
        refresh = await service.create_refresh_token(1)

        with pytest.raises(pyjwt.InvalidTokenError):
            await service.decode_access_token(refresh)

    async def test_rejects_tampered_signature(self, service: JWTService) -> None:
        """
        Тестируем: проверку подписи.
        Отдаём: access-токен, подписанный чужим секретом.
        Ожидаем: выброс jwt.InvalidTokenError.
        """
        forged = pyjwt.encode({"sub": "1", "type": "access"}, "other-secret", algorithm="HS256")

        with pytest.raises(pyjwt.InvalidTokenError):
            await service.decode_access_token(forged)

    async def test_ttl_reflects_expire_settings(self, service: JWTService) -> None:
        """
        Тестируем: остаток времени жизни токена.
        Отдаём: свежевыпущенный access-токен.
        Ожидаем: TTL в диапазоне (0, access_token_expire_minutes*60].
        """
        token = await service.create_access_token(1)

        ttl = await service.get_token_ttl_seconds(token)

        assert 0 < ttl <= settings.security.access_token_expire_minutes * 60
