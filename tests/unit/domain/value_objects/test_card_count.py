"""Юнит-тесты value object CardCount: границы валидации счётчика карточек."""

import pytest

from src.domain.exceptions import InvalidCardCountError
from src.domain.value_objects import CardCount


class TestCardCount:
    """Группа тестов счётчика карточек."""

    @pytest.mark.parametrize("valid", [0, 1, 100], ids=["zero", "one", "many"])
    def test_accepts_non_negative(self, valid: int) -> None:
        """
        Тестируем: создание счётчика карточек.
        Отдаём: неотрицательные целые числа.
        Ожидаем: объект создаётся и хранит значение.
        """
        assert CardCount(valid).value == valid

    @pytest.mark.parametrize("invalid", [-1, True, 2.5, "3"], ids=["negative", "bool", "float", "string"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию счётчика карточек.
        Отдаём: отрицательные и нецелые значения.
        Ожидаем: выброс InvalidCardCountError.
        """
        with pytest.raises(InvalidCardCountError):
            CardCount(invalid)
