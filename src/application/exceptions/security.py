"""Ошибки безопасности прикладного слоя."""

from __future__ import annotations

from src.application.exceptions.base import ApplicationError, ErrorCode


class SecurityViolationError(ApplicationError):
    """Нарушение требований безопасности при обработке запроса."""

    def __init__(self, message: str = "Запрос отклонён системой безопасности") -> None:
        """Инициализировать ошибку безопасности.

        Args:
            message: Текст сообщения об ошибке.
        """
        super().__init__(code=ErrorCode.UNAUTHORIZED, message=message)
