from src.application.exceptions.base import ApplicationError, ErrorCode


class CardOwnershipError(ApplicationError):
    """Карточка не принадлежит пользователю или не найдена."""

    def __init__(self, message: str = "Карточка не найдена") -> None:
        super().__init__(code=ErrorCode.NOT_FOUND, message=message)


class CardNotFoundError(ApplicationError):
    """Учебная карточка не найдена."""

    def __init__(self, message: str = "Карточка не найдена") -> None:
        super().__init__(code=ErrorCode.NOT_FOUND, message=message)


class NoCompletedCardsError(ApplicationError):
    """Нет завершённых карточек для операции."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class LlmRateLimitExceededError(ApplicationError):
    """Превышен лимит запросов к LLM."""

    def __init__(self, message: str = "Лимит генерации временно исчерпан") -> None:
        super().__init__(code=ErrorCode.SERVICE_UNAVAILABLE, message=message)


class CurrentBatchNotCompletedError(ApplicationError):
    """Текущая партия карточек ещё не завершена."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class InvalidTrackWorkSubmissionError(ApplicationError):
    """Некорректные ответы домашней работы по треку."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class TrackWorkUnavailableError(ApplicationError):
    """Домашняя работа по треку недоступна."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class InvalidSpeechWordsError(ApplicationError):
    """Некорректный список слов для речевой практики."""

    def __init__(self, message: str) -> None:
        super().__init__(code=ErrorCode.VALIDATION, message=message)


class SpeechRateLimitExceededError(ApplicationError):
    """Превышен лимит генерации речевой практики."""

    def __init__(self, message: str = "Лимит генерации временно исчерпан") -> None:
        super().__init__(code=ErrorCode.SERVICE_UNAVAILABLE, message=message)
