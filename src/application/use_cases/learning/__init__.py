"""Use cases модуля обучения.

Use cases сгруппированы по логическим направлениям:
``cards`` — учебные карточки, ``speech`` — речевая практика,
``work`` — работа по партии, ``export`` — экспорт материалов.
"""

from .cards import (
    CompleteCardUseCase,
    GenerateCardsUseCase,
    GetCardBatchStatusUseCase,
    GetCardPageUseCase,
    GetTrackPageUseCase,
    StartCardBatchGenerationUseCase,
)
from .export import ExportCardsToPDFUseCase
from .speech import GenerateSpeechPracticeUseCase, GetSpeechPracticePageUseCase
from .work import GetTrackWorkPageUseCase, SubmitTrackWorkUseCase

__all__ = [
    "CompleteCardUseCase",
    "ExportCardsToPDFUseCase",
    "GenerateCardsUseCase",
    "GenerateSpeechPracticeUseCase",
    "GetCardBatchStatusUseCase",
    "GetCardPageUseCase",
    "GetSpeechPracticePageUseCase",
    "GetTrackPageUseCase",
    "GetTrackWorkPageUseCase",
    "StartCardBatchGenerationUseCase",
    "SubmitTrackWorkUseCase",
]
