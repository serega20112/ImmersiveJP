from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.backend.dto.skill_dto import SkillAssessmentDTO


class TrustComponentDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    score: int
    note: str


class TrustScoreDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: int
    band_key: str
    band_title: str
    summary: str
    note: str
    components: list[TrustComponentDTO]


class TrackProgressDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    completed_cards: int
    generated_cards: int
    current_batch: int
    completion_rate: float
    completed_batches: int
    work_ready_batch: int | None = None


class ProgressReportDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_completed: int
    total_generated: int
    completion_rate: float
    next_step: str
    tracks: list[TrackProgressDTO]
    trust_score: TrustScoreDTO
    skill_assessment: SkillAssessmentDTO | None = None


class AIAdviceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    headline: str
    summary: str
    focus_points: list[str]


class DashboardSectionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    completed_cards: int
    generated_cards: int
    completion_rate: float
    completed_batches: int
    work_ready_batch: int | None = None
    href: str


class DashboardDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_display_name: str
    recommendation: str
    sections: list[DashboardSectionDTO]
    trust_score: TrustScoreDTO
    skill_assessment: SkillAssessmentDTO | None = None
    speech_practice_href: str


class PlanModuleDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    items: list[str] = Field(default_factory=list)


class PlanStageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int
    title: str
    timeframe: str
    summary: str
    status: str
    status_label: str
    focus_note: str | None = None
    modules: list[PlanModuleDTO] = Field(default_factory=list)


class PlanDictionaryLinkDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    href: str
    note: str


class PlanContentModeDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    summary: str
    next_shift_note: str
    rules: list[str] = Field(default_factory=list)
    dictionary_links: list[PlanDictionaryLinkDTO] = Field(default_factory=list)


class PlanPaceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    summary: str
    detail_note: str
    guidance: list[str] = Field(default_factory=list)


class LearningPlanPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    horizon_title: str
    horizon_note: str | None = None
    current_stage_title: str
    current_stage_timeframe: str
    current_stage_summary: str
    recovery_note: str | None = None
    next_action: str
    parallel_note: str
    content_mode: PlanContentModeDTO
    pace_mode: PlanPaceDTO
    stages: list[PlanStageDTO] = Field(default_factory=list)
