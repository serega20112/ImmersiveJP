"""
Юнит-тесты базовой доменной ошибки.

Проверяется: наследование от Exception, хранение message и details
и корректная строка приведения ошибки.
"""

import pytest

from src.domain.exceptions.base import DomainError


class TestDomainError:
    """Группа тестов базовой ошибки доменного слоя."""

    def test_stores_message_and_details(self) -> None:
        """
        Тестируем: хранение сообщения и деталей ошибки.
        Отдаём: сообщение и словарь деталей.
        Ожидаем: атрибуты заполнены, str() равен сообщению.
        """
        error = DomainError("Сбой", details={"field": "email"})

        assert error.message == "Сбой"
        assert error.details == {"field": "email"}
        assert str(error) == "Сбой"

    def test_details_default_to_empty_dict(self) -> None:
        """
        Тестируем: значение деталей по умолчанию.
        Отдаём: ошибку без details.
        Ожидаем: details — пустой словарь (не None).
        """
        assert DomainError("Сбой").details == {}

    @pytest.mark.parametrize("details", [{}, {"a": 1}], ids=["empty", "filled"])
    def test_is_exception_instance(self, details: dict) -> None:
        """
        Тестируем: принадлежность ошибки базовому классу исключений.
        Отдаём: ошибку с пустыми и заполненными деталями.
        Ожидаем: экземпляр является Exception.
        """
        assert isinstance(DomainError("msg", details=details), Exception)
