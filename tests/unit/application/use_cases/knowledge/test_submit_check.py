"""
Юнит-тесты use case SubmitKnowledgeCheckUseCase.

Проверяется отправка ответов на проверку знаний: передача вопросов в LLM-клиент,
маппинг результатов в DTO, сохранение списка вопросов и вычисление флага
успешного прохождения по порогу балла.
"""

from typing import Any

import pytest

from src.application.dto.knowledge import KnowledgeQuestionDTO
from src.application.use_cases.knowledge.submit_check import SubmitKnowledgeCheckUseCase


class _FakeLLMClient:
    """Подмена LLMClient: возвращает заготовленный результат оценки ответов."""

    def __init__(self, result: dict[str, Any]) -> None:
        """Инициализировать клиент результатом оценки.

        Args:
            result: Словарь, возвращаемый методом evaluate_knowledge_check.
        """
        self.result = result
        self.kwargs: dict[str, Any] = {}

    async def evaluate_knowledge_check(self, **kwargs: Any) -> dict[str, Any]:
        """Запомнить аргументы и вернуть результат оценки.

        Args:
            **kwargs: Именованные аргументы оценки.

        Returns:
            Словарь с полями score/summary/results.
        """
        self.kwargs = kwargs
        return self.result


def _questions() -> list[KnowledgeQuestionDTO]:
    """Собрать два вопроса проверки знаний.

    Returns:
        Список KnowledgeQuestionDTO.
    """
    return [
        KnowledgeQuestionDTO(id="q1", kind="translation", question="Переведи"),
        KnowledgeQuestionDTO(id="q2", kind="grammar", question="Частица", hints=["h1"]),
    ]


class TestSubmitKnowledgeCheckUseCase:
    """Группа тестов юзкейса отправки ответов на проверку знаний."""

    async def test_maps_results_and_keeps_questions(self) -> None:
        """
        Тестируем: маппинг результата оценки в страницу проверки.
        Отдаём: два вопроса и результат LLM с одним верным и одним неверным ответом.
        Ожидаем: вопросы сохранены без изменений; результаты преобразованы в DTO;
                 score и summary перенесены; LLM получил подготовленные вопросы.
        """
        result = {
            "score": 80,
            "summary": "Хорошо",
            "results": [
                {"question_id": "q1", "is_correct": True, "user_answer": "школа", "feedback": "верно"},
                {"question_id": "q2", "is_correct": False},
            ],
        }
        llm_client = _FakeLLMClient(result)
        questions = _questions()
        use_case = SubmitKnowledgeCheckUseCase(llm_client=llm_client)

        page = await use_case.execute(questions=questions, answers={"q1": "школа"})

        assert page.questions == questions
        assert page.score == 80
        assert page.summary == "Хорошо"
        assert page.passed is True
        assert [item.question_id for item in page.results] == ["q1", "q2"]
        assert page.results[0].is_correct is True
        assert page.results[1].user_answer == ""
        assert llm_client.kwargs["answers"] == {"q1": "школа"}

    @pytest.mark.parametrize(
        "score, expected_passed",
        [(0, False), (59, False), (60, True), (100, True)],
        ids=["zero", "just-below-threshold", "at-threshold", "perfect"],
    )
    async def test_passed_flag_follows_threshold(self, score: int, expected_passed: bool) -> None:
        """
        Тестируем: вычисление флага прохождения по порогу 60 баллов.
        Отдаём: результаты LLM с разными значениями score.
        Ожидаем: passed=True при score >= 60, иначе False.
        """
        llm_client = _FakeLLMClient({"score": score, "summary": "", "results": []})
        use_case = SubmitKnowledgeCheckUseCase(llm_client=llm_client)

        page = await use_case.execute(questions=_questions(), answers={})

        assert page.passed is expected_passed

    async def test_uses_defaults_when_result_is_empty(self) -> None:
        """
        Тестируем: обработку пустого результата оценки.
        Отдаём: LLM вернул пустой словарь.
        Ожидаем: score=0, summary пустой, результатов нет, passed=False.
        """
        use_case = SubmitKnowledgeCheckUseCase(llm_client=_FakeLLMClient({}))

        page = await use_case.execute(questions=_questions(), answers={})

        assert page.score == 0
        assert page.summary == ""
        assert page.results == []
        assert page.passed is False
