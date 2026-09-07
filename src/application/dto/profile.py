"""DTO профиля: прогресс, рекомендации, план обучения, доверие."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .skill import SkillAssessmentDTO


class TrustComponentDTO(BaseModel):
    """Один компонент оценки прогресса (trust score).

    Атрибуты:
        label: Название компонента.
        score: Числовая оценка компонента.
        note: Пояснение к оценке.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    score: int
    note: str


class TrustScoreDTO(BaseModel):
    """Итоговая оценка прогресса пользователя.

    Атрибуты:
        score: Числовая оценка.
        band_key: Ключ диапазона оценки.
        band_title: Название диапазона.
        summary: Текстовое резюме.
        note: Дополнительное пояснение.
        components: Составные части оценки.
    """

    model_config = ConfigDict(frozen=True)

    score: int
    band_key: str
    band_title: str
    summary: str
    note: str
    components: list[TrustComponentDTO]


class TrackProgressDTO(BaseModel):
    """Прогресс по одному треку.

    Атрибуты:
        track: Ключ трека.
        title: Название трека.
        completed_cards: Завершённые карточки.
        generated_cards: Созданные карточки.
        current_batch: Текущая партия.
        completion_rate: Доля завершения.
        completed_batches: Завершённые партии.
        work_ready_batch: Партия для работы (если доступна).
    """

    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    completed_cards: int
    generated_cards: int
    current_batch: int
    completion_rate: float
    completed_batches: int
    work_ready_batch: int | None = None


class ProgressReportDTO(BaseModel):
    """Итоговый отчёт о прогрессе пользователя.

    Атрибуты:
        total_completed: Всего завершённых карточек.
        total_generated: Всего созданных карточек.
        completion_rate: Общая доля завершения.
        next_step: Рекомендуемый следующий шаг.
        tracks: Прогресс по трекам.
        trust_score: Оценка прогресса.
        skill_assessment: Оценка навыков.
    """

    model_config = ConfigDict(frozen=True)

    total_completed: int
    total_generated: int
    completion_rate: float
    next_step: str
    tracks: list[TrackProgressDTO]
    trust_score: TrustScoreDTO
    skill_assessment: SkillAssessmentDTO | None = None


class AIAdviceDTO(BaseModel):
    """Персональный совет, сгенерированный ИИ.

    Атрибуты:
        headline: Заголовок совета.
        summary: Краткое резюме.
        focus_points: Ключевые пункты фокуса.
    """

    model_config = ConfigDict(frozen=True)

    headline: str
    summary: str
    focus_points: list[str]


class DashboardSectionDTO(BaseModel):
    """Секция дашборда для одного трека.

    Атрибуты:
        track: Ключ трека.
        title: Название секции.
        subtitle: Подзаголовок секции.
        completed_cards: Завершённые карточки.
        generated_cards: Созданные карточки.
        completion_rate: Доля завершения.
        completed_batches: Завершённые партии.
        work_ready_batch: Партия для работы.
        href: Ссылка на трек.
    """

    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    completed_cards: int
    generated_cards: int
    completion_rate: float
    completed_batches: int
    work_ready_batch: int | None = None
    href: str


class DashboardDTO(BaseModel):
    """Дашборд пользователя.

    Атрибуты:
        user_display_name: Имя пользователя.
        recommendation: Текстовая рекомендация.
        sections: Секции по трекам.
        trust_score: Оценка прогресса.
        skill_assessment: Оценка навыков.
        speech_practice_href: Ссылка на речевую практику.
    """

    model_config = ConfigDict(frozen=True)

    user_display_name: str
    recommendation: str
    sections: list[DashboardSectionDTO]
    trust_score: TrustScoreDTO
    skill_assessment: SkillAssessmentDTO | None = None
    speech_practice_href: str


class PlanModuleDTO(BaseModel):
    """Модуль учебного плана.

    Атрибуты:
        title: Название модуля.
        items: Пункты модуля.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    items: list[str] = Field(default_factory=list)


class PlanStageDTO(BaseModel):
    """Этап учебного плана.

    Атрибуты:
        index: Порядковый номер этапа.
        title: Название этапа.
        timeframe: Срок этапа.
        summary: Описание этапа.
        status: Машинный статус.
        status_label: Текстовый статус.
        focus_note: Пояснение фокуса этапа.
        modules: Модули этапа.
    """

    model_config = ConfigDict(frozen=True)

    index: int
    title: str
    timeframe: str
    summary: str
    status: str
    status_label: str
    focus_note: str | None = None
    modules: list[PlanModuleDTO] = Field(default_factory=list)


class PlanDictionaryLinkDTO(BaseModel):
    """Ссылка на справочные материалы.

    Атрибуты:
        label: Название ссылки.
        href: Адрес ссылки.
        note: Пояснение.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    href: str
    note: str


class PlanContentModeDTO(BaseModel):
    """Режим подачи контента в плане.

    Атрибуты:
        title: Название режима.
        summary: Описание режима.
        next_shift_note: Пояснение о смене режима.
        rules: Правила режима.
        dictionary_links: Справочные ссылки.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    summary: str
    next_shift_note: str
    rules: list[str] = Field(default_factory=list)
    dictionary_links: list[PlanDictionaryLinkDTO] = Field(default_factory=list)


class PlanPaceDTO(BaseModel):
    """Темп обучения в плане.

    Атрибуты:
        title: Название темпа.
        summary: Описание темпа.
        detail_note: Дополнительное пояснение.
        guidance: Рекомендации темпа.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    summary: str
    detail_note: str
    guidance: list[str] = Field(default_factory=list)


class LearningPlanPageDTO(BaseModel):
    """Страница учебного плана.

    Атрибуты:
        title: Заголовок страницы.
        subtitle: Подзаголовок страницы.
        horizon_title: Название горизонта планирования.
        horizon_note: Пояснение горизонта.
        current_stage_title: Текущий этап.
        current_stage_timeframe: Срок текущего этапа.
        current_stage_summary: Описание текущего этапа.
        recovery_note: Пояснение о восстановлении базы.
        next_action: Следующее действие.
        parallel_note: Пояснение о параллельных дорожках.
        content_mode: Режим контента.
        pace_mode: Темп обучения.
        stages: Этапы плана.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    horizon_title: str
    horizon_note: str | None = None
    current_stage_title: str
    current_stage_timeframe: str
    current_stage_summary: str
    recovery_note: str | None = None
    next_action: str
    parallel_note: str
    content_mode: PlanContentModeDTO
    pace_mode: PlanPaceDTO
    stages: list[PlanStageDTO] = Field(default_factory=list)
