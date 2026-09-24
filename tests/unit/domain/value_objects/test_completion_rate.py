"""
Юнит-тесты value object CompletionRate.

Проверяется: нормализация процента, ограничение диапазоном 0–100,
округление и приведение к строке.
"""

import pytest

from src.domain.exceptions import InvalidCompletionRateError
from src.domain.value_objects import CompletionRate
from src.domain.value_objects.completion_rate import CompletionRate as DirectImport


class TestCompletionRate:
    """Группа тестов процента завершения трека."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            (0, 0.0),
            (50, 50.0),
            (100, 100.0),
            (33.37, 33.4),
        ],
        ids=["zero", "half", "full", "rounded"],
    )
    def test_stores_valid_percentage(self, value: float, expected: float) -> None:
        """
        Тестируем: сохранение корректного процента завершения.
        Отдаём: числа в диапазоне 0–100, включая дробное.
        Ожидаем: значение приведено к float и округлено до десятых.
        """
        assert CompletionRate(value).percentage == pytest.approx(expected)

    @pytest.mark.parametrize(
        "value, expected",
        [(-10, 0.0), (150, 100.0)],
        ids=["clamped-low", "clamped-high"],
    )
    def test_clamps_out_of_range_values(self, value: float, expected: float) -> None:
        """
        Тестируем: ограничение процента диапазоном 0–100.
        Отдаём: значения ниже нуля и выше ста.
        Ожидаем: процент приведён к ближайшей границе диапазона.
        """
        assert CompletionRate(value).percentage == pytest.approx(expected)

    @pytest.mark.parametrize("invalid", ["50%", None, [50]], ids=["string", "none", "list"])
    def test_raises_on_non_numeric(self, invalid) -> None:
        """
        Тестируем: валидацию типа значения.
        Отдаём: нечисловые значения.
        Ожидаем: выброс InvalidCompletionRateError с деталями.
        """
        with pytest.raises(InvalidCompletionRateError) as exc_info:
            CompletionRate(invalid)

        assert exc_info.value.details == {"value": invalid}

    def test_str_formats_with_percent_sign(self) -> None:
        """
        Тестируем: строковое представление процента.
        Отдаём: значение 42.5.
        Ожидаем: строка вида «42.5%».
        """
        assert str(CompletionRate(42.5)) == "42.5%"

    def test_is_frozen_and_slots_based(self) -> None:
        """
        Тестируем: неизменяемость и экспорт из пакета.
        Отдаём: созданный экземпляр.
        Ожидаем: приведение к тому же классу из пакета, изменение запрещено.
        """
        rate = DirectImport(10)

        assert type(rate) is CompletionRate
        with pytest.raises(Exception):
            rate.percentage = 20  # type: ignore[misc]
