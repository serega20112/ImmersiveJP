from __future__ import annotations

from enum import StrEnum


class LearningGoal(StrEnum):
    TOURISM = "tourism"
    RELOCATION = "relocation"
    WORK = "work"
    UNIVERSITY = "university"


class LanguageLevel(StrEnum):
    ZERO = "zero"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
