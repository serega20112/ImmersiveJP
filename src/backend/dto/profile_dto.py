from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TrackProgressDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    completed_cards: int
    generated_cards: int
    current_batch: int
    completion_rate: float


class ProgressReportDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_completed: int
    total_generated: int
    completion_rate: float
    next_step: str
    tracks: list[TrackProgressDTO]


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
    href: str


class DashboardDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_display_name: str
    recommendation: str
    sections: list[DashboardSectionDTO]
