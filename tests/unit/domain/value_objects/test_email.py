"""
Юнит-тесты value object Email.

Проверяется валидация формата, нормализация регистра и пробелов,
а также поведение строкового представления.
"""

import pytest

from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects.email import Email


class TestEmailValueObject:
    """Группа тестов value object Email."""

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "plainaddress",
            "@no-local-part.com",
            "no-at-sign.com",
            "spaces in@email.com",
            "user@",
            "",
            "   ",
        ],
        ids=["no-at", "no-local-part", "no-domain-dot", "contains-spaces", "no-domain", "empty", "whitespace"],
    )
    def test_raises_when_email_format_is_invalid(self, invalid_email: str) -> None:
        """
        Тестируем: создание Email с некорректным форматом.
        Отдаём: набор заведомо невалидных email-строк.
        Ожидаем: выброс InvalidEmailError для каждого варианта.
        """
        with pytest.raises(InvalidEmailError):
            Email(invalid_email)

    @pytest.mark.parametrize(
        "raw_email, expected",
        [
            ("user@example.com", "user@example.com"),
            ("USER@Example.COM", "user@example.com"),
            ("  padded@example.com  ", "padded@example.com"),
            ("user.name+tag@example.co.uk", "user.name+tag@example.co.uk"),
        ],
        ids=["plain", "uppercase-normalized", "whitespace-stripped", "plus-tag"],
    )
    def test_normalizes_valid_email(self, raw_email: str, expected: str) -> None:
        """
        Тестируем: нормализацию валидного email.
        Отдаём: валидные строки с разным регистром и окружающими пробелами.
        Ожидаем: значение приводится к нижнему регистру без пробелов.
        """
        email = Email(raw_email)

        assert email.value == expected

    def test_str_returns_normalized_value(self) -> None:
        """
        Тестируем: строковое представление value object.
        Отдаём: валидный email в верхнем регистре.
        Ожидаем: str() возвращает нормализованное значение.
        """
        assert str(Email("USER@EXAMPLE.COM")) == "user@example.com"

    def test_equality_based_on_normalized_value(self) -> None:
        """
        Тестируем: сравнение двух value object Email.
        Отдаём: один и тот же адрес в разном регистре.
        Ожидаем: объекты равны после нормализации.
        """
        assert Email("User@Example.com") == Email("user@example.com")
