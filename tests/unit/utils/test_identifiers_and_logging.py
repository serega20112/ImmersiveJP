"""Юнит-тесты утилит identifiers и logging."""

import pytest

from src.utils.identifiers import to_optional, value_or_none
from src.utils.logging import get_logger, log_event


class TestToOptional:
    """Группа тестов конвертации значения в value object."""

    def test_applies_constructor_for_value(self) -> None:
        """
        Тестируем: применение конструктора к непустому значению.
        Отдаём: строку и конструктор, возвращающий длину.
        Ожидаем: результат конструктора.
        """
        assert to_optional("abc", len) == 3

    def test_returns_none_for_none(self) -> None:
        """
        Тестируем: None на входе.
        Отдаём: None.
        Ожидаем: None без вызова конструктора.
        """
        assert to_optional(None, len) is None


class TestValueOrNone:
    """Группа тестов извлечения значения из value object."""

    def test_extracts_value_attribute(self) -> None:
        """
        Тестируем: извлечение .value из объекта.
        Отдаём: объект с атрибутом value.
        Ожидаем: значение атрибута.
        """
        holder = type("Holder", (), {"value": 42})()

        assert value_or_none(holder) == 42

    def test_returns_object_without_value_attribute(self) -> None:
        """
        Тестируем: объект без атрибута value.
        Отдаём: обычную строку.
        Ожидаем: саму строку.
        """
        assert value_or_none("plain") == "plain"

    def test_returns_none_for_none(self) -> None:
        """
        Тестируем: None на входе.
        Отдаём: None.
        Ожидаем: None.
        """
        assert value_or_none(None) is None


class TestLoggingHelpers:
    """Группа тестов логгера и структурного события."""

    def test_get_logger_returns_named_logger(self) -> None:
        """
        Тестируем: получение логгера по имени.
        Отдаём: произвольное имя.
        Ожидаем: логгер с этим именем.
        """
        logger = get_logger("tests.sample")

        assert logger.name == "tests.sample"

    def test_log_event_emits_record_with_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        Тестируем: структурное событие в логе.
        Отдаём: INFO-событие с полями.
        Ожидаем: запись уровня INFO с атрибутом event.
        """
        logger = get_logger("tests.events")

        log_event(logger, 20, "sample.event", "Сообщение", user_id=1)

        record = caplog.records[-1]
        assert record.levelno == 20
        assert record.event == "sample.event"
        assert record.getMessage() == "Сообщение"
