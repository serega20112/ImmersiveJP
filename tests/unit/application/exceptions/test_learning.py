"""
Юнит-тесты исключений учебного процесса.

Проверяются: коды ошибок, сообщения по умолчанию для ошибок
с фиксированным текстом и переопределение сообщений.
"""

import pytest

from src.application.exceptions.base import ApplicationError, ErrorCode
from src.application.exceptions.learning import (
    CardNotFoundError,
    CardOwnershipError,
    CurrentBatchNotCompletedError,
    InvalidSpeechWordsError,
    InvalidTrackWorkSubmissionError,
    LlmRateLimitExceededError,
    NoCompletedCardsError,
    SpeechRateLimitExceededError,
    TrackWorkUnavailableError,
)


@pytest.mark.parametrize(
    "error, expected_code",
    [
        (CardOwnershipError(), ErrorCode.NOT_FOUND),
        (CardNotFoundError(), ErrorCode.NOT_FOUND),
        (NoCompletedCardsError("none"), ErrorCode.VALIDATION),
        (LlmRateLimitExceededError(), ErrorCode.SERVICE_UNAVAILABLE),
        (CurrentBatchNotCompletedError("not done"), ErrorCode.VALIDATION),
        (InvalidTrackWorkSubmissionError("bad"), ErrorCode.VALIDATION),
        (TrackWorkUnavailableError("n/a"), ErrorCode.VALIDATION),
        (InvalidSpeechWordsError("bad"), ErrorCode.VALIDATION),
        (SpeechRateLimitExceededError(), ErrorCode.SERVICE_UNAVAILABLE),
    ],
    ids=[
        "ownership",
        "not-found",
        "no-completed",
        "llm-rate-limit",
        "batch-not-completed",
        "invalid-work-submission",
        "work-unavailable",
        "invalid-speech-words",
        "speech-rate-limit",
    ],
)
def test_learning_errors_use_expected_codes(error: ApplicationError, expected_code: ErrorCode) -> None:
    """
    Тестируем: соответствие ошибки учебного процесса своему коду.
    Отдаём: экземпляр ошибки и ожидаемый код.
    Ожидаем: код ошибки совпадает с ожидаемым.
    """
    assert error.code is expected_code


@pytest.mark.parametrize(
    "error",
    [CardOwnershipError(), CardNotFoundError(), LlmRateLimitExceededError(), SpeechRateLimitExceededError()],
    ids=["ownership", "not-found", "llm-rate-limit", "speech-rate-limit"],
)
def test_default_messages_are_not_empty(error: ApplicationError) -> None:
    """
    Тестируем: сообщения ошибок с текстом по умолчанию.
    Отдаём: ошибки без явного сообщения.
    Ожидаем: message — непустая строка.
    """
    assert error.message


def test_messages_can_be_overridden() -> None:
    """
    Тестируем: переопределение текста сообщения.
    Отдаём: собственный текст в ошибку учебного процесса.
    Ожидаем: message равен переданному тексту.
    """
    assert NoCompletedCardsError("Пока нет карточек").message == "Пока нет карточек"
