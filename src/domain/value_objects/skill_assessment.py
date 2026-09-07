from dataclasses import dataclass

from src.domain.value_objects.user import LanguageLevel


@dataclass(frozen=True, slots=True)
class SkillAssessment:
    """Результат диагностики навыков пользователя."""

    score: int = 0
    estimated_level: LanguageLevel | None = None
    summary: str = ""
    strengths: tuple[str, ...] = ()
    weak_points: tuple[str, ...] = ()
