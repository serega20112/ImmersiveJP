"""
Юнит-тесты сервиса аутентификации.

AuthService — тонкий фасад над use case-объектами: проверяется, что каждый
метод передаёт дальше ровно те аргументы, что получил (в том числе None
для отсутствующих токенов), и возвращает результат use case без изменений.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.dto.auth import (
    AuthResultDTO,
    AuthTokensDTO,
    LoginDTO,
    RegistrationDTO,
    UserViewDTO,
    VerificationDTO,
)
from src.application.services import AuthService
from tests.fixtures.fakes import StubUseCase


def _user_view() -> UserViewDTO:
    """Собрать публичное представление пользователя для ответов-заглушек."""
    return UserViewDTO(
        id=1,
        email="a@a.com",
        display_name="Ая",
        is_email_verified=True,
        onboarding_completed=True,
    )


@dataclass
class AuthStubs:
    """Набор подменных use case-объектов сервиса аутентификации."""

    register: StubUseCase
    verify: StubUseCase
    login: StubUseCase
    logout: StubUseCase
    resolve: StubUseCase

    def build(self) -> AuthService:
        """Собрать AuthService поверх подменных use case-объектов.

        Returns:
            Сервис, все зависимости которого — заглушки.
        """
        return AuthService(
            register_user_use_case=self.register,
            verify_email_use_case=self.verify,
            login_user_use_case=self.login,
            logout_user_use_case=self.logout,
            resolve_current_user_use_case=self.resolve,
        )


@pytest.fixture
def auth_stubs() -> AuthStubs:
    """Заглушки use case-объектов аутентификации с предсказуемыми ответами."""
    return AuthStubs(
        register=StubUseCase(_user_view()),
        verify=StubUseCase(_user_view()),
        login=StubUseCase(
            AuthResultDTO(
                user=_user_view(),
                tokens=AuthTokensDTO(access_token="access", refresh_token="refresh"),
            )
        ),
        logout=StubUseCase(None),
        resolve=StubUseCase(_user_view()),
    )


class TestAuthServiceDelegation:
    """Группа тестов делегирования вызовов сервиса аутентификации."""

    async def test_register_forwards_payload(self, auth_stubs: AuthStubs) -> None:
        """
        Тестируем: делегирование регистрации в соответствующий use case.
        Отдаём: DTO регистрации с email, паролем и именем.
        Ожидаем: use case получил тот же payload, сервис вернул его DTO.
        """
        payload = RegistrationDTO(email="a@a.com", password="secret123", display_name="Ая")

        result = await auth_stubs.build().register(payload)

        assert auth_stubs.register.calls == [(payload,)]
        assert result.email == "a@a.com"

    async def test_verify_email_forwards_payload(self, auth_stubs: AuthStubs) -> None:
        """
        Тестируем: делегирование подтверждения email.
        Отдаём: DTO с email и кодом подтверждения.
        Ожидаем: use case получил тот же payload.
        """
        payload = VerificationDTO(email="a@a.com", code="123456")

        await auth_stubs.build().verify_email(payload)

        assert auth_stubs.verify.calls == [(payload,)]

    async def test_login_returns_tokens(self, auth_stubs: AuthStubs) -> None:
        """
        Тестируем: делегирование входа и возврат токенов.
        Отдаём: DTO входа с email и паролем.
        Ожидаем: use case получил payload, сервис вернул оба токена.
        """
        payload = LoginDTO(email="a@a.com", password="secret123")

        result = await auth_stubs.build().login(payload)

        assert auth_stubs.login.calls == [(payload,)]
        assert result.tokens.access_token == "access"
        assert result.tokens.refresh_token == "refresh"

    async def test_logout_forwards_both_tokens(self, auth_stubs: AuthStubs) -> None:
        """
        Тестируем: делегирование выхода с обоими токенами.
        Отдаём: access- и refresh-токены.
        Ожидаем: use case получил их позиционно в том же порядке.
        """
        await auth_stubs.build().logout("access", "refresh")

        assert auth_stubs.logout.calls == [("access", "refresh")]

    @pytest.mark.parametrize(
        "access_token",
        ["access", None],
        ids=["with-token", "without-token"],
    )
    async def test_resolve_current_user_forwards_token(
        self,
        auth_stubs: AuthStubs,
        access_token: str | None,
    ) -> None:
        """
        Тестируем: делегирование разрешения текущего пользователя.
        Отдаём: токен доступа и его отсутствие (None).
        Ожидаем: use case получил ровно переданное значение.
        """
        result = await auth_stubs.build().resolve_current_user(access_token)

        assert auth_stubs.resolve.calls == [(access_token,)]
        assert result is not None
