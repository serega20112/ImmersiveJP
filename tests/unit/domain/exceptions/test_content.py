"""
Юнит-тесты ошибок доменной области контента.

Проверяется: общий предок ContentDomainError и принадлежность
конкретных ошибок батча/позиции/завершения карточки этому предку.
"""

import pytest

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.content import (
    CardAlreadyCompletedError,
    ContentDomainError,
    InvalidBatchNumberError,
    InvalidCardPositionError,
)


class TestContentDomainErrors:
    """Группа тестов ошибок доменной области контента."""

    @pytest.mark.parametrize(
        "error_cls",
        [InvalidBatchNumberError, InvalidCardPositionError, CardAlreadyCompletedError],
        ids=["batch-number", "card-position", "already-completed"],
    )
    def test_inherits_content_domain_error(self, error_cls) -> None:
        """
        Тестируем: иерархию ошибок контента.
        Отдаём: класс конкретной ошибки.
        Ожидаем: экземпляр наследует ContentDomainError и DomainError.
        """
        error = error_cls("bad")

        assert isinstance(error, ContentDomainError)
        assert isinstance(error, DomainError)

    def test_keeps_message_and_details(self) -> None:
        """
        Тестируем: передачу сообщения и деталей конкретной ошибке.
        Отдаём: сообщение и словарь деталей.
        Ожидаем: атрибуты сохранены без изменений.
        """
        error = InvalidBatchNumberError("Номер батча неверен", details={"batch": -1})

        assert error.message == "Номер батча неверен"
        assert error.details == {"batch": -1}
