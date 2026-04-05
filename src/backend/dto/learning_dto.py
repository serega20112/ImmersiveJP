from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CardExampleDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_text: str
    japanese: str
    romaji: str | None = None
    translation: str | None = None


class TrackCardDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    track: str
    topic: str
    preview: str
    explanation: str
    examples: list[CardExampleDTO]
    key_terms: list[str]
    batch_number: int
    position: int
    is_completed: bool


class TrackPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    cards: list[TrackCardDTO]
    current_batch: int
    completed_total: int
    generated_total: int
    all_current_batch_completed: bool
    can_generate_next: bool


class TrackCardPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    card: TrackCardDTO
    batch_cards: list[TrackCardDTO]
    current_batch: int
    completed_total: int
    generated_total: int
    all_current_batch_completed: bool
    can_generate_next: bool


class CardCompletionResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    card_id: int
    track: str
    batch_completed: bool


class PdfDocumentDTO(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    filename: str
    content: bytes
    media_type: str = "application/pdf"


class GeneratedCardDraftDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic: str
    explanation: str
    examples: list[str]
    key_terms: list[str]
