"""
Юнит-тесты исключений аутентификации и регистрации.

Проверяются: коды ошибок, сообщения по умолчанию и возможность
передать собственный текст сообщения.
"""

import pytest

from src.application.exceptions.auth import (
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidRegistrationDataError,
    InvalidVerificationCodeError,
)
from src.application.exceptions.base import ApplicationError, ErrorCode


@pytest.mark.parametrize(
    "error, expected_code",
    [
        (EmailAlreadyExistsError(), ErrorCode.CONFLICT),
        (InvalidRegistrationDataError("bad"), ErrorCode.VALIDATION),
        (InvalidCredentialsError(), ErrorCode.UNAUTHENTICATED),
        (EmailNotVerifiedError(), ErrorCode.UNAUTHORIZED),
        (InvalidVerificationCodeError("bad"), ErrorCode.VALIDATION),
    ],
    ids=["already-exists", "invalid-registration", "invalid-credentials", "not-verified", "invalid-code"],
)
def test_auth_errors_use_expected_codes(error: ApplicationError, expected_code: ErrorCode) -> None:
    """
    Тестируем: соответствие ошибки аутентификации своему коду.
    Отдаём: экземпляр ошибки и ожидаемый код.
    Ожидаем: код ошибки совпадает с ожидаемым.
    """
    assert error.code is expected_code


def test_auth_errors_support_custom_message() -> None:
    """
    Тестируем: переопределение текста сообщения.
    Отдаём: собственное сообщение в каждую ошибку.
    Ожидаем: message равен переданному тексту.
    """
    error = EmailAlreadyExistsError("Такой email уже занят")

    assert error.message == "Такой email уже занят"


def test_default_messages_are_not_empty() -> None:
    """
    Тестируем: сообщения ошибок по умолчанию.
    Отдаём: ошибки без явного сообщения.
    Ожидаем: message — непустая строка.
    """
    for error in (EmailAlreadyExistsError(), InvalidCredentialsError(), EmailNotVerifiedError()):
        assert error.message
