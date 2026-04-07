from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.backend.dto.skill_dto import SkillAssessmentDTO


class DiagnosticOptionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str
    label: str
    description: str


class DiagnosticQuestionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    prompt: str
    skill_label: str
    options: list[DiagnosticOptionDTO]
    hints: list[str] = Field(default_factory=list)


class DiagnosticQuestionGroupDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: str
    title: str
    description: str
    questions: list[DiagnosticQuestionDTO] = Field(default_factory=list)


class StudyTimelineOptionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: str
    title: str
    description: str


class OnboardingPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    diagnostic_groups: list[DiagnosticQuestionGroupDTO] = Field(default_factory=list)
    study_timeline_options: list[StudyTimelineOptionDTO] = Field(default_factory=list)


class OnboardingDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal: str
    language_level: str
    study_timeline: str
    interests_text: str
    diagnostic_answers: dict[str, str] = Field(default_factory=dict)
    diagnostic_hints_used: int = 0


class OnboardingResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    generated_batches: dict[str, int]
    skill_assessment: SkillAssessmentDTO
