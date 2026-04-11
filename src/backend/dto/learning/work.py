from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.backend.dto.profile_dto import TrustScoreDTO


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
