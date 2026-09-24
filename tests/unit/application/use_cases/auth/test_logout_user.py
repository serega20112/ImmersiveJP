"""
Юнит-тесты use case LogoutUserUseCase.

Проверяется логика выхода из системы: отзыв access- и refresh-токенов
с остаточным TTL, а также пропуск отсутствующих (None/пустых) токенов
без обращения к блок-листу.
"""

import pytest

from src.application.use_cases.auth.logout_user import LogoutUserUseCase


class _FakeJwtService:
    """Подмена JWTService: возвращает предсказуемый остаток жизни токена."""

    def __init__(self, ttl: int = 120) -> None:
        """Инициализировать сервис фиксированным TTL.

        Args:
            ttl: Значение остаточного времени жизни токена в секундах.
        """
        self.ttl = ttl
        self.requested: list[str] = []

    async def get_token_ttl_seconds(self, token: str) -> int:
        """Запомнить токен и вернуть фиксированный TTL.

        Args:
            token: Разбираемый токен.

        Returns:
            Остаток времени жизни токена в секундах.
        """
        self.requested.append(token)
        return self.ttl


class _FakeTokenBlocklist:
    """Подмена TokenBlocklist: фиксирует отозванные токены и их TTL."""

    def __init__(self) -> None:
        """Инициализировать пустой журнал отзывов."""
        self.revoked: list[tuple[str, int]] = []

    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Запомнить отзыв токена.

        Args:
            token: Отзываемый токен.
            ttl_seconds: Время жизни, на которое токен помещается в блок-лист.
        """
        self.revoked.append((token, ttl_seconds))


@pytest.fixture
def jwt_service() -> _FakeJwtService:
    """Подменный JWT-сервис с остатком жизни токена 120 секунд."""
    return _FakeJwtService(ttl=120)


@pytest.fixture
def token_blocklist() -> _FakeTokenBlocklist:
    """Подменный блок-лист отозванных токенов."""
    return _FakeTokenBlocklist()


class TestLogoutUserUseCase:
    """Группа тестов юзкейса отзыва токенов при выходе."""

    async def test_revokes_both_tokens_with_their_ttl(self, jwt_service, token_blocklist) -> None:
        """
        Тестируем: отзыв обоих токенов при выходе.
        Отдаём: непустые access- и refresh-токены; JWT-сервис возвращает TTL=120.
        Ожидаем: каждый токен отозван в блок-листе с TTL 120, порядок сохранён.
        """
        use_case = LogoutUserUseCase(jwt_service=jwt_service, token_blocklist=token_blocklist)

        await use_case.execute(access_token="access-token", refresh_token="refresh-token")

        assert token_blocklist.revoked == [("access-token", 120), ("refresh-token", 120)]
        assert jwt_service.requested == ["access-token", "refresh-token"]

    @pytest.mark.parametrize(
        "access_token, refresh_token",
        [(None, None), ("", ""), (None, "refresh-token"), ("access-token", None)],
        ids=["both-none", "both-empty", "only-refresh", "only-access"],
    )
    async def test_skips_absent_tokens(self, jwt_service, token_blocklist, access_token, refresh_token) -> None:
        """
        Тестируем: пропуск отсутствующих токенов.
        Отдаём: комбинации с None/пустыми токенами, часть из которых задана.
        Ожидаем: отзываются только непустые токены; пустые игнорируются.
        """
        use_case = LogoutUserUseCase(jwt_service=jwt_service, token_blocklist=token_blocklist)

        await use_case.execute(access_token=access_token, refresh_token=refresh_token)

        expected = [token for token in (access_token, refresh_token) if token]
        assert [token for token, _ in token_blocklist.revoked] == expected
