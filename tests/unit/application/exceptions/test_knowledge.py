"""
Юнит-тесты исключения проверки знаний.

Проверяется: код VALIDATION, сообщение по умолчанию и возможность
передать собственный текст сообщения.
"""

from src.application.exceptions.base import ErrorCode
from src.application.exceptions.knowledge import InvalidKnowledgeDataError


class TestInvalidKnowledgeDataError:
    """Группа тестов ошибки некорректных данных проверки знаний."""

    def test_uses_validation_code(self) -> None:
        """
        Тестируем: код ошибки данных проверки знаний.
        Отдаём: ошибку с сообщением по умолчанию.
        Ожидаем: код VALIDATION, непустое сообщение.
        """
        error = InvalidKnowledgeDataError()

        assert error.code is ErrorCode.VALIDATION
        assert error.message

    def test_supports_custom_message(self) -> None:
        """
        Тестируем: переопределение текста сообщения.
        Отдаём: собственный текст.
        Ожидаем: message равен переданному тексту.
        """
        assert InvalidKnowledgeDataError("Свой текст").message == "Свой текст"
