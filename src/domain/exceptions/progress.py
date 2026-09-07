from .base import DomainError


class ProgressDomainError(DomainError):
    """Базовая ошибка доменной области прогресса."""


class InvalidCardCountError(ProgressDomainError):
    """Некорректное количество карточек."""


class InvalidCompletionRateError(ProgressDomainError):
    """Некорректный процент завершения."""
