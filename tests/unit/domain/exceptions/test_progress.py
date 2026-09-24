"""
Юнит-тесты ошибок доменной области прогресса.

Проверяется: наследование ProgressDomainError и принадлежность
ошибок счётчика карточек и процента завершения этому предку.
"""

import pytest

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.progress import (
    InvalidCardCountError,
    InvalidCompletionRateError,
    ProgressDomainError,
)


class TestProgressDomainErrors:
    """Группа тестов ошибок доменной области прогресса."""

    @pytest.mark.parametrize(
        "error_cls",
        [InvalidCardCountError, InvalidCompletionRateError],
        ids=["card-count", "completion-rate"],
    )
    def test_inherits_progress_domain_error(self, error_cls) -> None:
        """
        Тестируем: иерархию ошибок прогресса.
        Отдаём: класс конкретной ошибки.
        Ожидаем: экземпляр наследует ProgressDomainError и DomainError.
        """
        error = error_cls("bad")

        assert isinstance(error, ProgressDomainError)
        assert isinstance(error, DomainError)

    def test_keeps_details(self) -> None:
        """
        Тестируем: передачу деталей ошибке прогресса.
        Отдаём: словарь деталей с некорректным значением.
        Ожидаем: details сохранены.
        """
        assert InvalidCompletionRateError("bad", details={"value": None}).details == {"value": None}
