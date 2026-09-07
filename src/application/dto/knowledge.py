"""DTO проверки знаний: вопросы, ответы и страница проверки."""

from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.application.exceptions import InvalidKnowledgeDataError


class KnowledgeQuestionDTO(BaseModel):
    """Один вопрос проверки знаний.

    Атрибуты:
        id: Уникальный идентификатор вопроса.
        kind: Тип вопроса (перевод, грамматика, чтение и т.п.).
        question: Текст вопроса.
        context: Необязательный контекст для вопроса.
        hints: Подсказки для пользователя.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    kind: str
    question: str
    context: str = ""
    hints: list[str] = Field(default_factory=list)

    @classmethod
    def list_from_json(cls, raw: str) -> list[KnowledgeQuestionDTO]:
        """Разобрать JSON-строку с вопросами в список DTO.

        Args:
            raw: JSON-строка с вопросами (например, скрытое поле формы).

        Returns:
            Список разобранных вопросов.

        Raises:
            InvalidKnowledgeDataError: Если строка не является корректным JSON
                или вопросы не соответствуют схеме.
        """
        try:
            raw_questions = json.loads(raw)
            return [cls.model_validate(item) for item in raw_questions]
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
            raise InvalidKnowledgeDataError from error


class KnowledgeAnswerResultDTO(BaseModel):
    """Результат проверки одного ответа.

    Атрибуты:
        question_id: Идентификатор вопроса.
        is_correct: Корректность ответа.
        user_answer: Ответ пользователя.
        expected_answer: Правильный ответ.
        feedback: Обратная связь по ответу.
    """

    model_config = ConfigDict(frozen=True)

    question_id: str
    is_correct: bool
    user_answer: str
    expected_answer: str
    feedback: str


class KnowledgeCheckPageDTO(BaseModel):
    """Страница проверки знаний с вопросами и результатами.

    Атрибуты:
        title: Заголовок страницы.
        subtitle: Подзаголовок страницы.
        focus_area: Область фокуса проверки.
        questions: Список вопросов.
        results: Результаты проверки (заполняется после отправки).
        score: Общий балл.
        summary: Текстовое резюме.
        passed: Флаг успешного прохождения проверки.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    focus_area: str
    questions: list[KnowledgeQuestionDTO] = Field(default_factory=list)
    results: list[KnowledgeAnswerResultDTO] | None = None
    score: int | None = None
    summary: str | None = None
    passed: bool | None = None
