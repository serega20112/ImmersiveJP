"""
Юнит-тесты DTO проверки знаний.

Проверяются: значения по умолчанию, разбор JSON со списком вопросов
и обработка некорректных данных при разборе.
"""

import pytest

from src.application.dto.knowledge import (
    KnowledgeAnswerResultDTO,
    KnowledgeCheckPageDTO,
    KnowledgeQuestionDTO,
)
from src.application.exceptions import InvalidKnowledgeDataError


class TestKnowledgeQuestionDTO:
    """Группа тестов DTO одного вопроса проверки знаний."""

    def test_defaults_for_optional_fields(self) -> None:
        """
        Тестируем: значения по умолчанию контекста и подсказок.
        Отдаём: только обязательные поля вопроса.
        Ожидаем: context — пустая строка, hints — пустой список.
        """
        dto = KnowledgeQuestionDTO(id="q1", kind="translation", question="Как сказать «дом»?")

        assert dto.context == ""
        assert dto.hints == []

    def test_list_from_json_parses_valid_payload(self) -> None:
        """
        Тестируем: разбор корректной JSON-строки со списком вопросов.
        Отдаём: JSON с двумя вопросами.
        Ожидаем: список из двух DTO с сохранёнными идентификаторами.
        """
        raw = '[{"id": "q1", "kind": "translation", "question": "A"}, ' \
              '{"id": "q2", "kind": "grammar", "question": "B", "hints": ["h"]}]'

        questions = KnowledgeQuestionDTO.list_from_json(raw)

        assert [q.id for q in questions] == ["q1", "q2"]
        assert questions[1].hints == ["h"]

    @pytest.mark.parametrize(
        "raw",
        [
            "not-json",
            "{",
            '{"id": "q1"}',
            "[1, 2, 3]",
            "42",
        ],
        ids=["garbage", "broken-json", "not-a-list-of-questions", "list-of-ints", "scalar"],
    )
    def test_list_from_json_raises_on_invalid_payload(self, raw: str) -> None:
        """
        Тестируем: обработку некорректного содержимого JSON.
        Отдаём: строки с битым JSON и данными неверной схемы.
        Ожидаем: InvalidKnowledgeDataError для каждого варианта.
        """
        with pytest.raises(InvalidKnowledgeDataError):
            KnowledgeQuestionDTO.list_from_json(raw)


class TestKnowledgeCheckPageDTO:
    """Группа тестов DTO страницы проверки знаний."""

    def test_defaults_before_submission(self) -> None:
        """
        Тестируем: состояние страницы до отправки ответов.
        Отдаём: только заголовок, подзаголовок и область фокуса.
        Ожидаем: результаты и балл равны None, список вопросов пуст.
        """
        dto = KnowledgeCheckPageDTO(title="Проверка", subtitle="Подзаголовок", focus_area="grammar")

        assert dto.questions == []
        assert dto.results is None
        assert dto.score is None
        assert dto.passed is None

    def test_answer_result_keeps_feedback(self) -> None:
        """
        Тестируем: DTO результата одного ответа.
        Отдаём: заполненный результат проверки.
        Ожидаем: все поля сохранены без изменений.
        """
        dto = KnowledgeAnswerResultDTO(
            question_id="q1",
            is_correct=False,
            user_answer="いえ",
            expected_answer="はい",
            feedback="Почти!",
        )

        assert dto.is_correct is False
        assert dto.expected_answer == "はい"
