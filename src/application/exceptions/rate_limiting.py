"""Ошибки ограничения частоты запросов."""

from __future__ import annotations

from src.application.exceptions.base import ApplicationError, ErrorCode


class RateLimitExceededError(ApplicationError):
    """Превышен допустимый лимит запросов."""

    def __init__(
        self,
        *,
        limit: int,
        remaining: int = 0,
        retry_after_seconds: int,
    ) -> None:
        """Инициализировать ошибку rate limit.

        Args:
            limit: Максимальное количество запросов за окно.
            remaining: Оставшееся количество запросов.
            retry_after_seconds: Через сколько секунд можно повторить запрос.
        """
        self.limit = limit
        self.remaining = remaining
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message="Слишком много запросов. Попробуйте позже.",
            details={
                "limit": limit,
                "remaining": remaining,
                "retry_after_seconds": retry_after_seconds,
            },
        )
