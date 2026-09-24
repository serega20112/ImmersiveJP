"""Юнит-тесты value object CardPosition: валидация позиции карточки в батче."""

import pytest

from src.domain.exceptions import InvalidCardPositionError
from src.domain.value_objects import CardPosition


class TestCardPosition:
    """Группа тестов позиции карточки в батче."""

    def test_valid_value_and_conversions(self) -> None:
        """
        Тестируем: создание валидной позиции карточки.
        Отдаём: положительное целое число 5.
        Ожидаем: хранение значения, int() и str() согласованы.
        """
        position = CardPosition(5)

        assert position.value == 5
        assert int(position) == 5
        assert str(position) == "5"

    @pytest.mark.parametrize("invalid", [0, -2, True, 1.5, "2"], ids=["zero", "negative", "bool", "float", "string"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию позиции карточки.
        Отдаём: ноль, отрицательное, bool, дробное и строковое значения.
        Ожидаем: выброс InvalidCardPositionError.
        """
        with pytest.raises(InvalidCardPositionError):
            CardPosition(invalid)

    def test_equality_and_ordering(self) -> None:
        """
        Тестируем: сравнение позиций между собой и с int.
        Отдаём: позиции 1 и 2.
        Ожидаем: равенство с тем же числом, упорядочивание, совпадение хешей.
        """
        assert CardPosition(1) == 1
        assert CardPosition(1) < CardPosition(2)
        assert CardPosition(1) < 2
        assert hash(CardPosition(1)) == hash(CardPosition(1))
