"""Юнит-тесты value object SkillAssessment: значения по умолчанию и хранение."""

from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.user import LanguageLevel


class TestSkillAssessment:
    """Группа тестов результата диагностики навыков."""

    def test_defaults_are_neutral(self) -> None:
        """
        Тестируем: значения по умолчанию результата диагностики.
        Отдаём: SkillAssessment без аргументов.
        Ожидаем: нулевой счёт, пустые списки и неопределённый уровень.
        """
        assessment = SkillAssessment()

        assert assessment.score == 0
        assert assessment.estimated_level is None
        assert assessment.summary == ""
        assert assessment.strengths == ()
        assert assessment.weak_points == ()

    def test_accepts_estimated_level(self) -> None:
        """
        Тестируем: хранение оценённого уровня.
        Отдаём: счёт и уровень BASIC.
        Ожидаем: поля сохранены.
        """
        assessment = SkillAssessment(score=60, estimated_level=LanguageLevel.BASIC)

        assert assessment.score == 60
        assert assessment.estimated_level == LanguageLevel.BASIC
