"""Юнит-тесты value object DisplayName: нормализация и границы длины."""

import pytest

from src.domain.exceptions import InvalidDisplayNameError
from src.domain.value_objects import DisplayName


class TestDisplayName:
    """Группа тестов отображаемого имени пользователя."""

    @pytest.mark.parametrize(
        "raw, expected",
        [("Сергей", "Сергей"), ("  padded  ", "padded"), ("a", "a")],
        ids=["plain", "trimmed", "one-char"],
    )
    def test_accepts_and_normalizes(self, raw: str, expected: str) -> None:
        """
        Тестируем: создание отображаемого имени.
        Отдаём: строки в границах длины, в том числе с пробелами.
        Ожидаем: значение сохранено с обрезкой пробелов.
        """
        assert DisplayName(raw).value == expected

    @pytest.mark.parametrize("invalid", ["", "   ", "x" * 101, 123], ids=["empty", "whitespace", "too-long", "not-str"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию отображаемого имени.
        Отдаём: пустые строки, строку длиннее 100 символов и не-строку.
        Ожидаем: выброс InvalidDisplayNameError.
        """
        with pytest.raises(InvalidDisplayNameError):
            DisplayName(invalid)
