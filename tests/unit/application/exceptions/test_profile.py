"""
Юнит-тесты исключения профиля.

Проверяется: код VALIDATION и передача текста сообщения об
ошибке в сообщении наставнику.
"""

from src.application.exceptions.base import ErrorCode
from src.application.exceptions.profile import InvalidMentorMessageError


class TestInvalidMentorMessageError:
    """Группа тестов ошибки некорректного сообщения наставнику."""

    def test_uses_validation_code(self) -> None:
        """
        Тестируем: код ошибки сообщения наставнику.
        Отдаём: ошибку с сообщением.
        Ожидаем: код VALIDATION, message сохранён.
        """
        error = InvalidMentorMessageError("Пустое сообщение")

        assert error.code is ErrorCode.VALIDATION
        assert error.message == "Пустое сообщение"
