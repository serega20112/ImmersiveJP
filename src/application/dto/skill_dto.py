from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillAssessmentDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: int
    estimated_level: str | None = None
    estimated_level_title: str | None = None
    summary: str
    strengths: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
