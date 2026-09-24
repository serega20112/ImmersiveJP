"""
Юнит-тесты ошибки ограничения частоты запросов.

Проверяются: код RATE_LIMITED, сохранение параметров лимита
и наполнение деталей ошибки.
"""

import pytest

from src.application.exceptions.base import ErrorCode
from src.application.exceptions.rate_limiting import RateLimitExceededError


class TestRateLimitExceededError:
    """Группа тестов ошибки превышения лимита запросов."""

    def test_uses_rate_limited_code(self) -> None:
        """
        Тестируем: код ошибки лимита запросов.
        Отдаём: лимит и время до повтора.
        Ожидаем: код RATE_LIMITED, непустое сообщение.
        """
        error = RateLimitExceededError(limit=10, retry_after_seconds=30)

        assert error.code is ErrorCode.RATE_LIMITED
        assert error.message

    def test_keeps_limit_details(self) -> None:
        """
        Тестируем: сохранение параметров лимита в атрибутах и деталях.
        Отдаём: лимит 10, остаток 3, повтор через 30 секунд.
        Ожидаем: атрибуты и details отражают переданные значения.
        """
        error = RateLimitExceededError(limit=10, remaining=3, retry_after_seconds=30)

        assert (error.limit, error.remaining, error.retry_after_seconds) == (10, 3, 30)
        assert error.details == {"limit": 10, "remaining": 3, "retry_after_seconds": 30}

    def test_remaining_defaults_to_zero(self) -> None:
        """
        Тестируем: значение остатка запросов по умолчанию.
        Отдаём: лимит и время до повтора без остатка.
        Ожидаем: remaining равен 0.
        """
        error = RateLimitExceededError(limit=5, retry_after_seconds=60)

        assert error.remaining == 0

    @pytest.mark.parametrize("field", ["limit", "retry_after_seconds"])
    def test_requires_keyword_only_arguments(self, field: str) -> None:
        """
        Тестируем: обязательность keyword-only аргументов.
        Отдаём: попытку вызвать ошибку без одного из обязательных ключей.
        Ожидаем: TypeError.
        """
        kwargs = {"limit": 1, "retry_after_seconds": 1}
        kwargs.pop(field)

        with pytest.raises(TypeError):
            RateLimitExceededError(**kwargs)
