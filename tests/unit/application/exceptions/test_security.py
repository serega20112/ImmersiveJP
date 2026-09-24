"""
Юнит-тесты ошибки безопасности прикладного слоя.

Проверяется: код UNAUTHORIZED, сообщение по умолчанию
и возможность переопределить текст сообщения.
"""

from src.application.exceptions.base import ErrorCode
from src.application.exceptions.security import SecurityViolationError


class TestSecurityViolationError:
    """Группа тестов ошибки нарушения безопасности."""

    def test_uses_unauthorized_code(self) -> None:
        """
        Тестируем: код ошибки безопасности.
        Отдаём: ошибку с сообщением по умолчанию.
        Ожидаем: код UNAUTHORIZED, непустое сообщение.
        """
        error = SecurityViolationError()

        assert error.code is ErrorCode.UNAUTHORIZED
        assert error.message

    def test_supports_custom_message(self) -> None:
        """
        Тестируем: переопределение текста сообщения.
        Отдаём: собственный текст.
        Ожидаем: message равен переданному тексту.
        """
        assert SecurityViolationError("CSRF-токен неверен").message == "CSRF-токен неверен"
