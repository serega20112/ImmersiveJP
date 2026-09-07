from .base import DomainError


class UserDomainError(DomainError):
    """Базовая ошибка доменной сущности User."""


class InvalidEmailError(UserDomainError):
    """Некорректный формат email пользователя."""


class InvalidDisplayNameError(UserDomainError):
    """Некорректное отображаемое имя пользователя."""


class InvalidPasswordHashError(UserDomainError):
    """Некорректный хеш пароля пользователя."""


class UserAlreadyVerifiedError(UserDomainError):
    """Email пользователя уже подтверждён."""


class UserNotOnboardedError(UserDomainError):
    """Пользователь ещё не завершил онбординг."""
