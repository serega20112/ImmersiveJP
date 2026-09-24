"""
Юнит-тесты use case GenerateKnowledgeCheckUseCase.

Проверяется генерация страницы проверки знаний: ошибка при отсутствии
пользователя, проброс сильных/слабых сторон из отчёта в LLM-клиент,
маппинг сырых вопросов в DTO и обработка области фокуса.
"""

from typing import Any

import pytest

from src.application.dto.profile import ProgressReportDTO, TrustScoreDTO
from src.application.dto.skill import SkillAssessmentDTO
from src.application.use_cases.knowledge.generate_check import GenerateKnowledgeCheckUseCase
from tests.fixtures.factories.user_factory import UserFactory


def _report(skill: SkillAssessmentDTO | None) -> ProgressReportDTO:
    """Собрать отчёт о прогрессе с заданной оценкой навыков.

    Args:
        skill: Оценка навыков пользователя (или None).

    Returns:
        ProgressReportDTO с пустым набором треков.
    """
    return ProgressReportDTO(
        total_completed=0,
        total_generated=0,
        completion_rate=0.0,
        next_step="",
        tracks=[],
        trust_score=TrustScoreDTO(
            score=0,
            band_key="low",
            band_title="Низкий",
            summary="",
            note="",
            components=[],
        ),
        skill_assessment=skill,
    )


class _StubProgressReport:
    """Подмена BuildProgressReportUseCase с фиксированным отчётом."""

    def __init__(self, report: ProgressReportDTO) -> None:
        """Инициализировать заглушку отчётом.

        Args:
            report: Отчёт, возвращаемый методом execute.
        """
        self.report = report

    async def execute(self, user_id: int) -> ProgressReportDTO:  # noqa: ARG002
        """Вернуть заданный отчёт.

        Args:
            user_id: Идентификатор пользователя (не используется).

        Returns:
            Отчёт о прогрессе.
        """
        return self.report


class _FakeLLMClient:
    """Подмена LLMClient: возвращает заготовленные вопросы и фиксирует аргументы."""

    def __init__(self, questions: list[dict[str, Any]]) -> None:
        """Инициализировать клиент списком сырых вопросов.

        Args:
            questions: Вопросы, возвращаемые методом generate_knowledge_check.
        """
        self.questions = questions
        self.kwargs: dict[str, Any] = {}

    async def generate_knowledge_check(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Запомнить аргументы вызова и вернуть заготовленные вопросы.

        Args:
            **kwargs: Именованные аргументы генерации.

        Returns:
            Список сырых вопросов.
        """
        self.kwargs = kwargs
        return self.questions


_RAW_QUESTIONS = [
    {"id": "q1", "kind": "translation", "question": "Как сказать 'школа'?"},
    {"id": "q2", "kind": "grammar", "question": "Выбери частицу", "context": "ctx", "hints": ["h1"]},
]


class TestGenerateKnowledgeCheckUseCase:
    """Группа тестов юзкейса генерации проверки знаний."""

    async def test_raises_when_user_not_found(self, fake_uow) -> None:
        """
        Тестируем: генерацию проверки для несуществующего пользователя.
        Отдаём: пустой репозиторий пользователей.
        Ожидаем: выброс ValueError.
        """
        use_case = GenerateKnowledgeCheckUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report(None)),
            llm_client=_FakeLLMClient([]),
        )

        with pytest.raises(ValueError, match="Пользователь не найден"):
            await use_case.execute(user_id=1)

    async def test_maps_raw_questions_to_dto(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: маппинг сырых вопросов LLM в KnowledgeQuestionDTO.
        Отдаём: существующий пользователь; два вопроса, у второго есть context и hints.
        Ожидаем: вопросы преобразованы в DTO, необязательные поля первого
                 вопроса заполнены значениями по умолчанию.
        """
        fake_user_repository._by_id[3] = UserFactory().build(user_id=3)
        llm_client = _FakeLLMClient(_RAW_QUESTIONS)
        use_case = GenerateKnowledgeCheckUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report(None)),
            llm_client=llm_client,
        )

        page = await use_case.execute(user_id=3)

        assert [question.id for question in page.questions] == ["q1", "q2"]
        assert page.questions[0].context == ""
        assert page.questions[0].hints == []
        assert page.questions[1].hints == ["h1"]

    async def test_defaults_focus_area_to_general(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: обработку пустой области фокуса.
        Отдаём: focus_area не задан (пустая строка).
        Ожидаем: в странице focus_area равен "общая".
        """
        fake_user_repository._by_id[3] = UserFactory().build(user_id=3)
        use_case = GenerateKnowledgeCheckUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report(None)),
            llm_client=_FakeLLMClient([]),
        )

        page = await use_case.execute(user_id=3)

        assert page.focus_area == "общая"

    async def test_forwards_skill_points_to_llm(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: проброс сильных и слабых сторон из отчёта в LLM-клиент.
        Отдаём: отчёт с оценкой навыков (strengths/weak_points) и focus_area="грамматика".
        Ожидаем: LLM-клиент получил списки strengths/weak_points и переданный focus_area.
        """
        fake_user_repository._by_id[3] = UserFactory().build(user_id=3)
        skill = SkillAssessmentDTO(
            score=4,
            summary="ok",
            strengths=["чтение"],
            weak_points=["грамматика"],
        )
        llm_client = _FakeLLMClient([])
        use_case = GenerateKnowledgeCheckUseCase(
            uow=fake_uow,
            build_progress_report_use_case=_StubProgressReport(_report(skill)),
            llm_client=llm_client,
        )

        page = await use_case.execute(user_id=3, focus_area="грамматика")

        assert llm_client.kwargs["weak_points"] == ["грамматика"]
        assert llm_client.kwargs["strengths"] == ["чтение"]
        assert llm_client.kwargs["focus_area"] == "грамматика"
        assert page.focus_area == "грамматика"
