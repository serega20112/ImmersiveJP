"""
Юнит-тесты ошибок доменной области сессии.

Проверяется: наследование SessionDomainError и сохранение сообщения.
"""

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.session import SessionDomainError


class TestSessionDomainError:
    """Группа тестов базовой ошибки доменной области сессии."""

    def test_inherits_domain_error(self) -> None:
        """
        Тестируем: иерархию ошибки сессии.
        Отдаём: ошибку с сообщением.
        Ожидаем: наследует DomainError, message сохранён.
        """
        error = SessionDomainError("Сессия истекла")

        assert isinstance(error, DomainError)
        assert error.message == "Сессия истекла"
