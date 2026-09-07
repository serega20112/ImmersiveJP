"""DTO онбординга: диагностика, цели и результат первичной настройки."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .skill import SkillAssessmentDTO


class DiagnosticOptionDTO(BaseModel):
    """Один вариант ответа в диагностическом вопросе.

    Атрибуты:
        value: Машинное значение варианта.
        label: Человекочитаемая подпись.
        description: Расширенное описание варианта.
    """

    model_config = ConfigDict(frozen=True)

    value: str
    label: str
    description: str


class DiagnosticQuestionDTO(BaseModel):
    """Вопрос диагностики уровня знаний.

    Атрибуты:
        key: Уникальный ключ вопроса.
        prompt: Текст вопроса.
        skill_label: Название навыка, который проверяется.
        options: Варианты ответа.
        hints: Подсказки к вопросу.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    prompt: str
    skill_label: str
    options: list[DiagnosticOptionDTO]
    hints: list[str] = Field(default_factory=list)


class DiagnosticQuestionGroupDTO(BaseModel):
    """Группа диагностических вопросов одного уровня.

    Атрибуты:
        level: Ключ уровня сложности.
        title: Название группы.
        description: Описание группы.
        questions: Вопросы группы.
    """

    model_config = ConfigDict(frozen=True)

    level: str
    title: str
    description: str
    questions: list[DiagnosticQuestionDTO] = Field(default_factory=list)


class StudyTimelineOptionDTO(BaseModel):
    """Вариант желаемого срока обучения.

    Атрибуты:
        value: Машинное значение варианта.
        title: Название варианта.
        description: Описание варианта.
    """

    model_config = ConfigDict(frozen=True)

    value: str
    title: str
    description: str


class OnboardingPageDTO(BaseModel):
    """Страница онбординга с диагностикой и выбором целей.

    Атрибуты:
        diagnostic_groups: Группы диагностических вопросов.
        study_timeline_options: Варианты срока обучения.
    """

    model_config = ConfigDict(frozen=True)

    diagnostic_groups: list[DiagnosticQuestionGroupDTO] = Field(default_factory=list)
    study_timeline_options: list[StudyTimelineOptionDTO] = Field(default_factory=list)


class OnboardingDTO(BaseModel):
    """Данные формы онбординга пользователя.

    Атрибуты:
        goal: Цель обучения.
        language_level: Текущий уровень языка.
        study_timeline: Желаемый срок обучения.
        interests_text: Свободный текст интересов.
        diagnostic_answers: Ответы на диагностические вопросы.
        diagnostic_hints_used: Количество использованных подсказок.
    """

    model_config = ConfigDict(frozen=True)

    goal: str
    language_level: str
    study_timeline: str
    interests_text: str
    diagnostic_answers: dict[str, str] = Field(default_factory=dict)
    diagnostic_hints_used: int = 0


class OnboardingResultDTO(BaseModel):
    """Результат завершения онбординга.

    Атрибуты:
        user_id: Идентификатор пользователя.
        generated_batches: Количество созданных партий по трекам.
        skill_assessment: Оценка навыков пользователя.
    """

    model_config = ConfigDict(frozen=True)

    user_id: int
    generated_batches: dict[str, int]
    skill_assessment: SkillAssessmentDTO
