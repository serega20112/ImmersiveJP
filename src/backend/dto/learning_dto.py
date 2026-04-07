from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.backend.dto.profile_dto import TrustScoreDTO


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


class SpeechLineDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    japanese: str
    romaji: str | None = None
    translation: str | None = None


class SpeechDialogueTurnDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    speaker: str
    japanese: str
    romaji: str | None = None
    translation: str | None = None


class SpeechDialogueDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    scenario: str
    turns: list[SpeechDialogueTurnDTO] = Field(default_factory=list)


class SpeechPracticeDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    words: list[str] = Field(default_factory=list)
    sentences: list[SpeechLineDTO] = Field(default_factory=list)
    dialogues: list[SpeechDialogueDTO] = Field(default_factory=list)
    coaching_tip: str
    difficulty_label: str


class SpeechPracticePageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    words_text: str
    suggested_words: list[str] = Field(default_factory=list)
    latest_topics: list[str] = Field(default_factory=list)
    skill_summary: str | None = None
    practice: SpeechPracticeDTO | None = None


class WorkHintDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    content: str


class TrackWorkTaskDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: str
    title: str
    prompt: str
    expected_format: str
    source_topic: str
    placeholder: str
    required_terms: list[str] = Field(default_factory=list)
    hints: list[WorkHintDTO] = Field(default_factory=list)
    submitted_answer: str | None = None


class TrackWorkTaskResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    task_id: str
    is_correct: bool
    feedback: str
    revealed_answer: str | None = None


class TrackWorkResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: int
    pass_score: int
    passed: bool
    summary: str
    verdict: str
    certificate_statement: str | None = None
    task_results: list[TrackWorkTaskResultDTO] = Field(default_factory=list)


class TrackWorkPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    batch_number: int
    source_topics: list[str] = Field(default_factory=list)
    pass_score: int
    tasks: list[TrackWorkTaskDTO] = Field(default_factory=list)
    trust_score: TrustScoreDTO | None = None
    result: TrackWorkResultDTO | None = None
