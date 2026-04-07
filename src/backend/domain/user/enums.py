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


class StudyTimeline(StrEnum):
    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
    ONE_YEAR = "one_year"
    TWO_YEARS = "two_years"
    FLEXIBLE = "flexible"
