from src.application.exceptions.base import ApplicationError, ErrorCode


class InvalidMentorMessageError(ApplicationError):
    """Некорректное сообщение для наставника."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)
