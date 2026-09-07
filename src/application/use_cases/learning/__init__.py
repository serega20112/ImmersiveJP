"""Use cases модуля обучения.

Use cases сгруппированы по логическим направлениям:
``cards`` — учебные карточки, ``speech`` — речевая практика,
``work`` — работа по партии, ``export`` — экспорт материалов.
"""

from .cards import (
    CompleteCardUseCase,
    GenerateCardsUseCase,
    GetCardPageUseCase,
    GetNextCardsUseCase,
    GetTrackPageUseCase,
    RepairCurrentBatchUseCase,
)
from .export import ExportCardsToPDFUseCase
from .speech import GenerateSpeechPracticeUseCase, GetSpeechPracticePageUseCase
from .work import GetTrackWorkPageUseCase, SubmitTrackWorkUseCase

__all__ = [
    "CompleteCardUseCase",
    "ExportCardsToPDFUseCase",
    "GenerateCardsUseCase",
    "GenerateSpeechPracticeUseCase",
    "GetCardPageUseCase",
    "GetNextCardsUseCase",
    "GetSpeechPracticePageUseCase",
    "GetTrackPageUseCase",
    "GetTrackWorkPageUseCase",
    "RepairCurrentBatchUseCase",
    "SubmitTrackWorkUseCase",
]
