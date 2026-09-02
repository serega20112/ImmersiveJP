from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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
