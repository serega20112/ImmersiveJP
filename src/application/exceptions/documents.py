"""Исключения пользовательских документов."""

from src.application.exceptions.base import ApplicationError, ErrorCode


class InvalidDocumentDataError(ApplicationError):
    """Некорректные данные документа, отклонённые доменом."""

    def __init__(self, message: str = "Документ не принят") -> None:
        """Инициализировать ошибку данных документа.

        Args:
            message: Текст ошибки для пользователя.
        """
        super().__init__(code=ErrorCode.VALIDATION, message=message)
