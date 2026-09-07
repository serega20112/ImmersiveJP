from src.application.exceptions.base import ApplicationError, ErrorCode


class InvalidOnboardingDataError(ApplicationError):
    """Некорректные данные онбординга."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)
