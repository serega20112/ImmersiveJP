from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.domain.user.enums import LanguageLevel


@dataclass(slots=True)
class SkillAssessment:
    score: int = 0
    estimated_level: LanguageLevel | None = None
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weak_points: list[str] = field(default_factory=list)
