"""
Юнит-тесты ошибок доменной сущности User.

Проверяется: общий предок UserDomainError и принадлежность
ошибок email, имени, пароля и статусов пользователя этому предку.
"""

import pytest

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.user import (
    InvalidDisplayNameError,
    InvalidEmailError,
    InvalidPasswordHashError,
    UserAlreadyVerifiedError,
    UserDomainError,
    UserNotOnboardedError,
)


class TestUserDomainErrors:
    """Группа тестов ошибок доменной сущности User."""

    @pytest.mark.parametrize(
        "error_cls",
        [
            InvalidEmailError,
            InvalidDisplayNameError,
            InvalidPasswordHashError,
            UserAlreadyVerifiedError,
            UserNotOnboardedError,
        ],
        ids=["email", "display-name", "password-hash", "already-verified", "not-onboarded"],
    )
    def test_inherits_user_domain_error(self, error_cls) -> None:
        """
        Тестируем: иерархию ошибок пользователя.
        Отдаём: класс конкретной ошибки.
        Ожидаем: экземпляр наследует UserDomainError и DomainError.
        """
        error = error_cls("bad")

        assert isinstance(error, UserDomainError)
        assert isinstance(error, DomainError)

    @pytest.mark.parametrize(
        "error_cls, details",
        [
            (InvalidEmailError, {"value": "bad"}),
            (InvalidDisplayNameError, {"field": "display_name"}),
        ],
        ids=["email", "display-name"],
    )
    def test_keeps_details(self, error_cls, details: dict) -> None:
        """
        Тестируем: передачу деталей ошибке пользователя.
        Отдаём: словарь деталей конкретного вида.
        Ожидаем: details сохранены без изменений.
        """
        assert error_cls("bad", details=details).details == details
