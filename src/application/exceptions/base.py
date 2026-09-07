from enum import Enum


class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    VALIDATION = "VALIDATION"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    UNAUTHORIZED = "UNAUTHORIZED"
    INTERNAL = "INTERNAL"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"


class ApplicationError(Exception):
    """Базовая ошибка application-слоя."""

    def __init__(self, *, code: ErrorCode, message: str, details: dict | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ComponentUnavailableError(ApplicationError):
    """Компонент системы не отвечает."""

    def __init__(self, *, field: str | None = None, value: bool | None = None) -> None:
        details = {}
        if field and value is not None:
            details[field] = value
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Компонент системы не отвечает",
            details=details,
        )
