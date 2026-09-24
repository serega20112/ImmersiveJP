"""
Юнит-тесты исключения онбординга.

Проверяется: код VALIDATION и передача текста сообщения.
"""

from src.application.exceptions.base import ErrorCode
from src.application.exceptions.onboarding import InvalidOnboardingDataError


class TestInvalidOnboardingDataError:
    """Группа тестов ошибки некорректных данных онбординга."""

    def test_uses_validation_code(self) -> None:
        """
        Тестируем: код ошибки данных онбординга.
        Отдаём: ошибку с сообщением.
        Ожидаем: код VALIDATION, message равен переданному тексту.
        """
        error = InvalidOnboardingDataError("Слишком короткие интересы")

        assert error.code is ErrorCode.VALIDATION
        assert error.message == "Слишком короткие интересы"
