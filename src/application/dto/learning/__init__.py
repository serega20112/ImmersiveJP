"""Публичные DTO модуля обучения: карточки, документы, речь, работа."""

from .cards import (
    CardCompletionResultDTO,
    CardExampleDTO,
    GeneratedCardDraftDTO,
    KeyTermDTO,
    TrackCardDTO,
    TrackCardPageDTO,
    TrackPageDTO,
)
from .documents import PdfDocumentDTO
from .speech import (
    SpeechDialogueDTO,
    SpeechDialogueTurnDTO,
    SpeechLineDTO,
    SpeechPracticeDTO,
    SpeechPracticePageDTO,
)
from .work import (
    TrackWorkPageDTO,
    TrackWorkResultDTO,
    TrackWorkTaskDTO,
    TrackWorkTaskResultDTO,
    WorkHintDTO,
)

__all__ = [
    "CardCompletionResultDTO",
    "CardExampleDTO",
    "GeneratedCardDraftDTO",
    "KeyTermDTO",
    "PdfDocumentDTO",
    "SpeechDialogueDTO",
    "SpeechDialogueTurnDTO",
    "SpeechLineDTO",
    "SpeechPracticeDTO",
    "SpeechPracticePageDTO",
    "TrackCardDTO",
    "TrackCardPageDTO",
    "TrackPageDTO",
    "TrackWorkPageDTO",
    "TrackWorkResultDTO",
    "TrackWorkTaskDTO",
    "TrackWorkTaskResultDTO",
    "WorkHintDTO",
]
