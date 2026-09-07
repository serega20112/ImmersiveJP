from .base import DomainError


class InvalidTimestampValueError(DomainError):
    """Некорректное значение времени."""


class InvalidIDValueError(DomainError):
    """Некорректное значение идентификатора."""
