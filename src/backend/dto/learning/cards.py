from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CardExampleDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_text: str
    japanese: str
    romaji: str | None = None
    translation: str | None = None


class KeyTermDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_text: str
    label: str
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
    key_term_items: list[KeyTermDTO] = Field(default_factory=list)
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
    completed_batches: int
    work_ready_batch: int | None = None
    work_href: str | None = None


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
    completed_batches: int
    work_ready_batch: int | None = None
    work_href: str | None = None


class CardCompletionResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    card_id: int
    track: str
    batch_completed: bool


class GeneratedCardDraftDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic: str
    explanation: str
    examples: list[str]
    key_terms: list[str]
