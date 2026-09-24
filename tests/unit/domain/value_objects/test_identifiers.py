"""Юнит-тесты целочисленных идентификаторов на базе IntID."""

import pytest

from src.domain.exceptions import InvalidIDValueError
from src.domain.value_objects import UserID
from src.domain.value_objects.identifiers import LearningCardID, UserDocumentID


class TestIntegerIdentifiers:
    """Группа тестов идентификаторов пользователя, карточки и документа."""

    def test_stores_value_and_converts(self) -> None:
        """
        Тестируем: создание идентификатора пользователя.
        Отдаём: положительное целое число 7.
        Ожидаем: свойство value, int() и str() согласованы.
        """
        user_id = UserID(7)

        assert user_id.value == 7
        assert int(user_id) == 7
        assert str(user_id) == "7"

    @pytest.mark.parametrize("invalid", [0, -1, True, 1.5, "5"], ids=["zero", "negative", "bool", "float", "string"])
    def test_raises_on_invalid_value(self, invalid) -> None:
        """
        Тестируем: валидацию идентификатора.
        Отдаём: ноль, отрицательное, bool, дробное и строковое значения.
        Ожидаем: выброс InvalidIDValueError.
        """
        with pytest.raises(InvalidIDValueError):
            UserID(invalid)

    def test_types_are_isolated(self) -> None:
        """
        Тестируем: неравенство разных типов идентификаторов с одинаковым значением.
        Отдаём: UserID, LearningCardID и UserDocumentID со значением 1.
        Ожидаем: UserID равен только UserID того же значения.
        """
        assert UserID(1) == UserID(1)
        assert UserID(1) != LearningCardID(1)
        assert LearningCardID(1) != UserDocumentID(1)
