"""
Юнит-тесты ошибок доменных value object'ов.

Проверяется: принадлежность ошибок времени и идентификатора
базовой доменной ошибке и сохранение деталей.
"""

import pytest

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.value_objects import InvalidIDValueError, InvalidTimestampValueError


class TestValueObjectDomainErrors:
    """Группа тестов ошибок value object'ов."""

    @pytest.mark.parametrize(
        "error_cls",
        [InvalidIDValueError, InvalidTimestampValueError],
        ids=["id", "timestamp"],
    )
    def test_inherits_domain_error(self, error_cls) -> None:
        """
        Тестируем: иерархию ошибок value object'ов.
        Отдаём: класс конкретной ошибки.
        Ожидаем: экземпляр наследует DomainError напрямую.
        """
        error = error_cls("bad")

        assert isinstance(error, DomainError)
        assert type(error).__mro__[1] is DomainError

    def test_keeps_details(self) -> None:
        """
        Тестируем: передачу деталей ошибке идентификатора.
        Отдаём: словарь с некорректным значением.
        Ожидаем: details сохранены.
        """
        assert InvalidIDValueError("bad", details={"value": -1}).details == {"value": -1}
