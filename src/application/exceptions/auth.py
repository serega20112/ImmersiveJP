from src.application.exceptions.base import ApplicationError, ErrorCode


class EmailAlreadyExistsError(ApplicationError):
    """Пользователь с таким email уже существует."""

    def __init__(self, message: str = "Пользователь с таким email уже существует") -> None:
        super().__init__(code=ErrorCode.CONFLICT, message=message)


class InvalidRegistrationDataError(ApplicationError):
    """Некорректные данные регистрации."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class InvalidCredentialsError(ApplicationError):
    """Неверный email или пароль."""

    def __init__(self, message: str = "Неверный email или пароль") -> None:
        super().__init__(code=ErrorCode.UNAUTHENTICATED, message=message)


class EmailNotVerifiedError(ApplicationError):
    """Email пользователя ещё не подтверждён."""

    def __init__(self, message: str = "Сначала подтверди почту") -> None:
        super().__init__(code=ErrorCode.UNAUTHORIZED, message=message)


class InvalidVerificationCodeError(ApplicationError):
    """Неверный или просроченный код подтверждения."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)
