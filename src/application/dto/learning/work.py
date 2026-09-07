"""DTO работы по партии: задания, результаты, страница работы."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..profile import TrustScoreDTO


class WorkHintDTO(BaseModel):
    """Подсказка к заданию.

    Атрибуты:
        title: Название подсказки.
        content: Текст подсказки.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    content: str


class TrackWorkTaskDTO(BaseModel):
    """Задание в работе по партии.

    Атрибуты:
        id: Идентификатор задания.
        kind: Тип задания.
        title: Название задания.
        prompt: Формулировка задания.
        expected_format: Ожидаемый формат ответа.
        source_topic: Тема-источник задания.
        placeholder: Заполнитель поля ответа.
        required_terms: Обязательные термины.
        hints: Подсказки к заданию.
        submitted_answer: Ответ пользователя.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    kind: str
    title: str
    prompt: str
    expected_format: str
    source_topic: str
    placeholder: str
    required_terms: list[str] = Field(default_factory=list)
    hints: list[WorkHintDTO] = Field(default_factory=list)
    submitted_answer: str | None = None


class TrackWorkTaskResultDTO(BaseModel):
    """Результат проверки одного задания.

    Атрибуты:
        task_id: Идентификатор задания.
        is_correct: Корректность ответа.
        feedback: Обратная связь по ответу.
        revealed_answer: Правильный ответ.
    """

    model_config = ConfigDict(frozen=True)

    task_id: str
    is_correct: bool
    feedback: str
    revealed_answer: str | None = None


class TrackWorkResultDTO(BaseModel):
    """Итоговый результат работы по партии.

    Атрибуты:
        score: Набранные баллы.
        pass_score: Проходной балл.
        passed: Флаг успешного прохождения.
        summary: Резюме результата.
        verdict: Текстовый вердикт.
        certificate_statement: Поздравление с сертификатом.
        task_results: Результаты по заданиям.
    """

    model_config = ConfigDict(frozen=True)

    score: int
    pass_score: int
    passed: bool
    summary: str
    verdict: str
    certificate_statement: str | None = None
    task_results: list[TrackWorkTaskResultDTO] = Field(default_factory=list)


class TrackWorkPageDTO(BaseModel):
    """Страница работы по партии.

    Атрибуты:
        track: Ключ трека.
        title: Название страницы.
        subtitle: Подзаголовок страницы.
        batch_number: Номер партии.
        source_topics: Темы партии.
        pass_score: Проходной балл.
        tasks: Задания работы.
        trust_score: Оценка прогресса.
        result: Результат отправки.
    """

    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    batch_number: int
    source_topics: list[str] = Field(default_factory=list)
    pass_score: int
    tasks: list[TrackWorkTaskDTO] = Field(default_factory=list)
    trust_score: TrustScoreDTO | None = None
    result: TrackWorkResultDTO | None = None
