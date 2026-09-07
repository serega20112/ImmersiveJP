"""Исключения проверки знаний."""

from src.application.exceptions.base import ApplicationError, ErrorCode


class InvalidKnowledgeDataError(ApplicationError):
    """Некорректные данные проверки знаний в запросе."""

    def __init__(
        self,
        message: str = "Не удалось прочитать тест. Сгенерируйте новый.",
    ) -> None:
        """Инициализировать ошибку данных проверки знаний.

        Args:
            message: Текст ошибки для пользователя.
        """
        super().__init__(code=ErrorCode.VALIDATION, message=message)
