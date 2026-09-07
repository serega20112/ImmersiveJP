"""DTO оценки навыков пользователя."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillAssessmentDTO(BaseModel):
    """Результат диагностики уровня навыков.

    Атрибуты:
        score: Числовая оценка навыков.
        estimated_level: Ключевой уровень (например, ``basic``).
        estimated_level_title: Человекочитаемое название уровня.
        summary: Текстовое резюме диагностики.
        strengths: Сильные стороны пользователя.
        weak_points: Слабые стороны пользователя.
    """

    model_config = ConfigDict(frozen=True)

    score: int
    estimated_level: str | None = None
    estimated_level_title: str | None = None
    summary: str
    strengths: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
