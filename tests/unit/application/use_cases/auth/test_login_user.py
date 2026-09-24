"""
Юнит-тесты use case LoginUserUseCase.

Проверяются: успешный вход с выдачей токенов, неверные учётные данные,
неподтверждённый email и некорректный формат email.
"""

import pytest

from src.application.dto.auth import LoginDTO
from src.application.exceptions import EmailNotVerifiedError, InvalidCredentialsError
from tests.fixtures.fakes import FakePasswordService


class _FakeJwtService:
    """Подмена JWTService с детерминированными токенами."""

    async def create_access_token(self, user_id: int) -> str:
        """Вернуть детерминированный access-токен.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Строка вида "access:<id>".
        """
        return f"access:{user_id}"

    async def create_refresh_token(self, user_id: int) -> str:
        """Вернуть детерминированный refresh-токен.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Строка вида "refresh:<id>".
        """
        return f"refresh:{user_id}"


@pytest.fixture
def jwt_service() -> _FakeJwtService:
    """Подменный JWT-сервис для тестов входа."""
    return _FakeJwtService()


class TestLoginUserUseCase:
    """Группа тестов юзкейса входа пользователя."""

    @pytest.fixture
    def jwt_service(self) -> _FakeJwtService:
        """Подменный JWT-сервис для тестов входа."""
        return _FakeJwtService()

    async def test_login_returns_user_and_tokens(self, fake_uow, fake_user_repository, user_factory, jwt_service) -> None:
        """
        Тестируем: успешную аутентификацию.
        Отдаём: подтверждённый пользователь в репозитории и пароль,
                из которого фабрика построила его хеш ("hashed-password" -> "hashed:hashed-password").
        Ожидаем: AuthResultDTO с данными пользователя и парой токенов.
        """
        from src.application.use_cases.auth.login_user import LoginUserUseCase

        user = user_factory.build(user_id=5, password_hash="hashed:hashed-password")
        user.is_email_verified = True
        fake_user_repository._by_email[user.email.value] = user
        use_case = LoginUserUseCase(fake_uow, FakePasswordService(), jwt_service)

        result = await use_case.execute(LoginDTO(email="user@example.com", password="hashed-password"))

        assert result.user.id == 5
        assert result.tokens.access_token == "access:5"
        assert result.tokens.refresh_token == "refresh:5"

    async def test_rejects_wrong_password(self, fake_uow, fake_user_repository, user_factory, jwt_service) -> None:
        """
        Тестируем: вход с неверным паролем.
        Отдаём: существующий пользователь и неверный пароль.
        Ожидаем: выброс InvalidCredentialsError.
        """
        from src.application.use_cases.auth.login_user import LoginUserUseCase

        user = user_factory.build(user_id=5)
        user.is_email_verified = True
        fake_user_repository._by_email[user.email.value] = user
        use_case = LoginUserUseCase(fake_uow, FakePasswordService(), jwt_service)

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(email="user@example.com", password="wrong"))

    async def test_rejects_unknown_email(self, fake_uow, jwt_service) -> None:
        """
        Тестируем: вход с незарегистрированным email.
        Отдаём: пустой репозиторий и валидный, но неизвестный email.
        Ожидаем: выброс InvalidCredentialsError.
        """
        from src.application.use_cases.auth.login_user import LoginUserUseCase

        use_case = LoginUserUseCase(fake_uow, FakePasswordService(), jwt_service)

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(email="ghost@example.com", password="whatever1"))

    async def test_rejects_unverified_email(self, fake_uow, fake_user_repository, user_factory, jwt_service) -> None:
        """
        Тестируем: вход до подтверждения почты.
        Отдаём: пользователь с is_email_verified=False и верным паролем.
        Ожидаем: выброс EmailNotVerifiedError.
        """
        from src.application.use_cases.auth.login_user import LoginUserUseCase

        user = user_factory.build(user_id=5, password_hash="hashed:hashed-password")
        user.is_email_verified = False
        fake_user_repository._by_email[user.email.value] = user
        use_case = LoginUserUseCase(fake_uow, FakePasswordService(), jwt_service)

        with pytest.raises(EmailNotVerifiedError):
            await use_case.execute(LoginDTO(email="user@example.com", password="hashed-password"))

    async def test_rejects_malformed_email(self, fake_uow, jwt_service) -> None:
        """
        Тестируем: вход с некорректным форматом email.
        Отдаём: строку без @.
        Ожидаем: выброс InvalidCredentialsError (не InvalidEmailError).
        """
        from src.application.use_cases.auth.login_user import LoginUserUseCase

        use_case = LoginUserUseCase(fake_uow, FakePasswordService(), jwt_service)

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(email="not-an-email", password="whatever1"))
