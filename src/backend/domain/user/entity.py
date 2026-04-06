from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.backend.domain.user.enums import LanguageLevel, LearningGoal
from src.backend.domain.user.skill_assessment import SkillAssessment


@dataclass(slots=True)
class User:
    email: str
    password_hash: str
    display_name: str
    is_email_verified: bool = False
    learning_goal: LearningGoal | None = None
    language_level: LanguageLevel | None = None
    interests: list[str] = field(default_factory=list)
    onboarding_completed: bool = False
    skill_assessment: SkillAssessment | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
