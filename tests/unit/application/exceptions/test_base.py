"""
Юнит-тесты базовых исключений прикладного слоя.

Проверяются: перечень кодов ошибок, хранение сообщения и деталей,
а также наполнение деталей у ошибки недоступного компонента.
"""

import pytest

from src.application.exceptions.base import (
    ApplicationError,
    ComponentUnavailableError,
    ErrorCode,
)


class TestErrorCode:
    """Группа тестов перечня кодов ошибок прикладного слоя."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("NOT_FOUND", "NOT_FOUND"),
            ("ALREADY_EXISTS", "ALREADY_EXISTS"),
            ("VALIDATION", "VALIDATION"),
            ("UNAUTHENTICATED", "UNAUTHENTICATED"),
            ("UNAUTHORIZED", "UNAUTHORIZED"),
            ("INTERNAL", "INTERNAL"),
            ("SERVICE_UNAVAILABLE", "SERVICE_UNAVAILABLE"),
            ("CONFLICT", "CONFLICT"),
            ("RATE_LIMITED", "RATE_LIMITED"),
        ],
        ids=str.lower,
    )
    def test_code_equals_its_name(self, name: str, expected: str) -> None:
        """
        Тестируем: значение каждого кода ошибки.
        Отдаём: имя члена перечисления.
        Ожидаем: значение совпадает с именем (str-Enum).
        """
        assert ErrorCode[name] == expected


class TestApplicationError:
    """Группа тестов базовой ошибки приложения."""

    def test_stores_code_message_and_details(self) -> None:
        """
        Тестируем: хранение кода, сообщения и деталей ошибки.
        Отдаём: код, сообщение и словарь деталей.
        Ожидаем: все атрибуты заполнены, str() равен сообщению.
        """
        error = ApplicationError(code=ErrorCode.VALIDATION, message="Плохо", details={"f": 1})

        assert error.code is ErrorCode.VALIDATION
        assert error.message == "Плохо"
        assert error.details == {"f": 1}
        assert str(error) == "Плохо"

    def test_details_default_to_empty_dict(self) -> None:
        """
        Тестируем: значение деталей по умолчанию.
        Отдаём: ошибку без details.
        Ожидаем: details — пустой словарь (не None).
        """
        error = ApplicationError(code=ErrorCode.INTERNAL, message="Сбой")

        assert error.details == {}


class TestComponentUnavailableError:
    """Группа тестов ошибки недоступного компонента."""

    def test_uses_service_unavailable_code(self) -> None:
        """
        Тестируем: код ошибки недоступного компонента.
        Отдаём: ошибку без параметров.
        Ожидаем: код SERVICE_UNAVAILABLE, детали пусты.
        """
        error = ComponentUnavailableError()

        assert error.code is ErrorCode.SERVICE_UNAVAILABLE
        assert error.details == {}

    def test_adds_detail_when_field_and_value_given(self) -> None:
        """
        Тестируем: наполнение деталей при переданных field и value.
        Отдаём: имя поля и булево значение.
        Ожидаем: детали содержат пару поле/значение.
        """
        error = ComponentUnavailableError(field="database", value=False)

        assert error.details == {"database": False}

    @pytest.mark.parametrize(
        "field, value",
        [(None, False), ("database", None)],
        ids=["without-field", "without-value"],
    )
    def test_skips_detail_when_part_is_missing(self, field, value) -> None:
        """
        Тестируем: пропуск деталей при неполной паре field/value.
        Отдаём: только имя поля или только значение.
        Ожидаем: детали остаются пустыми.
        """
        assert ComponentUnavailableError(field=field, value=value).details == {}
