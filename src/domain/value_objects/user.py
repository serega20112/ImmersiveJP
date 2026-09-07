from enum import StrEnum


class LanguageLevel(StrEnum):
    """Уровень владения языком."""

    ZERO = "zero"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"


class LearningGoal(StrEnum):
    """Цель изучения японского."""

    TOURISM = "tourism"
    RELOCATION = "relocation"
    WORK = "work"
    UNIVERSITY = "university"


class StudyTimeline(StrEnum):
    """Желаемые сроки обучения."""

    THREE_MONTHS = "three_months"
    SIX_MONTHS = "six_months"
    ONE_YEAR = "one_year"
    TWO_YEARS = "two_years"
    FLEXIBLE = "flexible"
