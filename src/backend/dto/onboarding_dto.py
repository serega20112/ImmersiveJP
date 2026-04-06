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


class OnboardingPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    diagnostic_questions: list[DiagnosticQuestionDTO] = Field(default_factory=list)


class OnboardingDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal: str
    language_level: str
    interests_text: str
    diagnostic_answers: dict[str, str] = Field(default_factory=dict)


class OnboardingResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    generated_batches: dict[str, int]
    skill_assessment: SkillAssessmentDTO
