"""Юнит-фикстуры: моки портов приложения и готовые use case-объекты."""

from __future__ import annotations

from typing import Any

import pytest

from src.application.use_cases.auth.register_user import RegisterUserUseCase
from tests.fixtures.fakes import FakePasswordService, FakeUnitOfWork, FakeUserRepository


class FakeVerificationStore:
    """Подмена EmailVerificationStore: коды хранятся в словаре."""

    def __init__(self) -> None:
        """Инициализировать пустое хранилище кодов."""
        self.issued: dict[str, str] = {}

    async def issue_code(self, email: str) -> str:
        """Выдать и сохранить детерминированный числовой код подтверждения.

        Args:
            email: Адрес электронной почты.

        Returns:
            Шестизначный числовой код (как в реальном хранилище).
        """
        code = "".join(str(ord(ch) % 10) for ch in email[:6].ljust(6, "0"))
        self.issued[email] = code
        return code

    async def verify_code(self, email: str, code: str) -> bool:
        """Проверить код подтверждения и погасить его при совпадении.

        Args:
            email: Адрес электронной почты.
            code: Проверяемый код.

        Returns:
            True, если код совпадает с выданным ранее.
        """
        if self.issued.get(email) == code:
            del self.issued[email]
            return True
        return False


class FakeMailer:
    """Подмена Mailer: письма складываются в список для проверок."""

    def __init__(self) -> None:
        """Инициализировать пустой список отправленных писем."""
        self.sent: list[tuple[str, str]] = []

    async def send_verification_code(self, email: str, code: str) -> None:
        """Запомнить отправленный код подтверждения.

        Args:
            email: Адрес получателя.
            code: Код подтверждения.
        """
        self.sent.append((email, code))


@pytest.fixture
def fake_user_repository() -> FakeUserRepository:
    """Пустой in-memory репозиторий пользователей."""
    return FakeUserRepository()


@pytest.fixture
def fake_uow(fake_user_repository: FakeUserRepository) -> FakeUnitOfWork:
    """Unit of Work с репозиторием "user" поверх fake-репозитория."""
    return FakeUnitOfWork({"user": fake_user_repository})


@pytest.fixture
def password_service() -> FakePasswordService:
    """Фейковый сервис хеширования паролей."""
    return FakePasswordService()


@pytest.fixture
def verification_store() -> FakeVerificationStore:
    """Фейковое хранилище кодов подтверждения email."""
    return FakeVerificationStore()


@pytest.fixture
def mailer() -> FakeMailer:
    """Фейковый отправитель писем."""
    return FakeMailer()


@pytest.fixture
def register_use_case(
    fake_uow: FakeUnitOfWork,
    password_service: FakePasswordService,
    verification_store: FakeVerificationStore,
    mailer: FakeMailer,
) -> RegisterUserUseCase:
    """RegisterUserUseCase, собранный целиком на подменных зависимостях."""
    return RegisterUserUseCase(
        uow=fake_uow,
        password_service=password_service,
        verification_store=verification_store,
        mailer=mailer,
    )


class Recorder:
    """Минимальный recorder-объект для фиксации вызовов в тестах."""

    def __init__(self) -> None:
        """Инициализировать пустой журнал вызовов."""
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def record(self, name: str, *args: Any) -> None:
        """Добавить вызов в журнал.

        Args:
            name: Имя вызванного метода.
            *args: Аргументы вызова.
        """
        self.calls.append((name, args))
