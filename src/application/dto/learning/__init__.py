"""Публичные DTO модуля обучения: карточки, документы, речь, работа."""

from .cards import (
    CardBatchStatusDTO,
    CardCompletionResultDTO,
    CardExampleDTO,
    GeneratedCardBatchDTO,
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
    PreparedWorkTaskDTO,
    TrackWorkPageDTO,
    TrackWorkResultDTO,
    TrackWorkTaskDTO,
    TrackWorkTaskResultDTO,
    WorkHintDTO,
)

__all__ = [
    "CardBatchStatusDTO",
    "CardCompletionResultDTO",
    "CardExampleDTO",
    "GeneratedCardDraftDTO",
    "GeneratedCardBatchDTO",
    "KeyTermDTO",
    "PdfDocumentDTO",
    "PreparedWorkTaskDTO",
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
