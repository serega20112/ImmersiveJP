"""
Юнит-тесты DTO оценки навыков.

Проверяются: обязательность полей, значения по умолчанию
и изоляция списков сильных/слабых сторон.
"""

from src.application.dto.skill import SkillAssessmentDTO


class TestSkillAssessmentDTO:
    """Группа тестов DTO результата диагностики навыков."""

    def test_optional_fields_default_to_empty(self) -> None:
        """
        Тестируем: значения по умолчанию необязательных полей.
        Отдаём: только балл и текстовое резюме.
        Ожидаем: уровень равен None, списки сильных/слабых сторон пусты.
        """
        dto = SkillAssessmentDTO(score=42, summary="Средний уровень")

        assert dto.estimated_level is None
        assert dto.estimated_level_title is None
        assert dto.strengths == []
        assert dto.weak_points == []

    def test_lists_are_isolated_between_instances(self) -> None:
        """
        Тестируем: изоляцию default_factory для списков навыков.
        Отдаём: два DTO, мутацию списка первого.
        Ожидаем: списки второго экземпляра не затрагиваются.
        """
        first = SkillAssessmentDTO(score=1, summary="a")
        second = SkillAssessmentDTO(score=2, summary="b")

        first.strengths.append("лексика")
        first.weak_points.append("грамматика")

        assert second.strengths == []
        assert second.weak_points == []
