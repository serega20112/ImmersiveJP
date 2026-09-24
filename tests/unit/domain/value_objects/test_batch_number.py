"""Юнит-тесты value object BatchNumber: валидация, сравнение, конверсии."""

import pytest

from src.domain.exceptions import InvalidBatchNumberError
from src.domain.value_objects import BatchNumber


class TestBatchNumber:
    """Группа тестов номера батча учебных карточек."""

    def test_valid_value_and_conversions(self) -> None:
        """
        Тестируем: создание валидного номера батча.
        Отдаём: положительное целое число 3.
        Ожидаем: хранение значения, int() и str() возвращают 3 и "3".
        """
        batch = BatchNumber(3)

        assert batch.value == 3
        assert int(batch) == 3
        assert str(batch) == "3"

    @pytest.mark.parametrize("invalid", [0, -1, True, 1.5, "2"], ids=["zero", "negative", "bool", "float", "string"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию номера батча.
        Отдаём: ноль, отрицательное, bool, дробное и строковое значения.
        Ожидаем: выброс InvalidBatchNumberError для каждого варианта.
        """
        with pytest.raises(InvalidBatchNumberError):
            BatchNumber(invalid)

    def test_equality_and_ordering(self) -> None:
        """
        Тестируем: сравнение номеров батчей между собой и с int.
        Отдаём: номера 2 и 3.
        Ожидаем: равенство с тем же числом, строгое упорядочивание, совпадение хешей.
        """
        assert BatchNumber(2) == 2
        assert BatchNumber(2) == BatchNumber(2)
        assert BatchNumber(2) < BatchNumber(3)
        assert BatchNumber(2) < 3
        assert hash(BatchNumber(2)) == hash(BatchNumber(2))
