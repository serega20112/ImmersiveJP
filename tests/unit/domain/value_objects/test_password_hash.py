"""
Юнит-тесты value object PasswordHash.

Проверяется: валидация непустого значения, сохранение хеша
и строковое представление.
"""

import pytest

from src.domain.exceptions import InvalidPasswordHashError
from src.domain.value_objects import PasswordHash


class TestPasswordHash:
    """Группа тестов хеша пароля пользователя."""

    @pytest.mark.parametrize(
        "value",
        ["$2b$12$abcdefghijklmnopqrstuv", "hashed-password", "x"],
        ids=["bcrypt-like", "plain", "single-char"],
    )
    def test_stores_non_empty_hash(self, value: str) -> None:
        """
        Тестируем: сохранение непустого хеша.
        Отдаём: непустые строки разной длины.
        Ожидаем: значение сохранено, str() совпадает с ним.
        """
        password_hash = PasswordHash(value)

        assert password_hash.value == value
        assert str(password_hash) == value

    @pytest.mark.parametrize("invalid", ["", "   ", "\n\t"], ids=["empty", "spaces", "whitespace"])
    def test_raises_on_blank_value(self, invalid: str) -> None:
        """
        Тестируем: валидацию пустого или пробельного хеша.
        Отдаём: пустые и состоящие из пробелов строки.
        Ожидаем: выброс InvalidPasswordHashError с полем password_hash.
        """
        with pytest.raises(InvalidPasswordHashError) as exc_info:
            PasswordHash(invalid)

        assert exc_info.value.details == {"field": "password_hash"}

    def test_is_frozen(self) -> None:
        """
        Тестируем: неизменяемость value object'а.
        Отдаём: созданный хеш и попытку изменить значение.
        Ожидаем: исключение при присваивании.
        """
        password_hash = PasswordHash("hashed")

        with pytest.raises(Exception):
            password_hash.value = "other"  # type: ignore[misc]
