"""DTO учебных карточек: примеры, термины, страницы треков."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CardExampleDTO(BaseModel):
    """Один пример употребления в учебной карточке.

    Атрибуты:
        raw_text: Исходный текст примера.
        japanese: Пример на японском.
        romaji: Транслитерация (ромадзи).
        translation: Перевод примера.
    """

    model_config = ConfigDict(frozen=True)

    raw_text: str
    japanese: str
    romaji: str | None = None
    translation: str | None = None


class KeyTermDTO(BaseModel):
    """Ключевой термин учебной карточки.

    Атрибуты:
        raw_text: Исходное написание термина.
        label: Основное значение.
        translation: Перевод термина.
    """

    model_config = ConfigDict(frozen=True)

    raw_text: str
    label: str
    translation: str | None = None


class TrackCardDTO(BaseModel):
    """Учебная карточка в составе партии.

    Атрибуты:
        id: Идентификатор карточки.
        track: Ключ трека.
        topic: Тема карточки.
        preview: Краткое превью объяснения.
        explanation: Развёрнутое объяснение.
        examples: Примеры употребления.
        key_terms: Список ключевых терминов.
        key_term_items: Структурированные ключевые термины.
        batch_number: Номер партии.
        position: Позиция в партии.
        is_completed: Флаг завершения карточки.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    track: str
    topic: str
    preview: str
    explanation: str
    examples: list[CardExampleDTO]
    key_terms: list[str]
    key_term_items: list[KeyTermDTO] = Field(default_factory=list)
    batch_number: int
    position: int
    is_completed: bool


class TrackPageDTO(BaseModel):
    """Страница трека со списком карточек текущей партии.

    Атрибуты:
        track: Ключ трека.
        title: Название трека.
        subtitle: Подзаголовок трека.
        cards: Карточки текущей партии.
        current_batch: Текущая партия.
        completed_total: Завершённые карточки.
        generated_total: Созданные карточки.
        all_current_batch_completed: Флаг завершения текущей партии.
        can_generate_next: Флаг доступности генерации следующей партии.
        generate_action_label: Текст кнопки генерации.
        completed_batches: Завершённые партии.
        work_ready_batch: Партия для работы.
        work_href: Ссылка на работу.
    """

    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    cards: list[TrackCardDTO]
    current_batch: int
    completed_total: int
    generated_total: int
    all_current_batch_completed: bool
    can_generate_next: bool
    generate_action_label: str
    completed_batches: int
    work_ready_batch: int | None = None
    work_href: str | None = None


class TrackCardPageDTO(BaseModel):
    """Страница отдельной карточки внутри партии.

    Атрибуты:
        track: Ключ трека.
        title: Название трека.
        subtitle: Подзаголовок трека.
        card: Текущая карточка.
        batch_cards: Все карточки партии.
        current_batch: Текущая партия.
        completed_total: Завершённые карточки.
        generated_total: Созданные карточки.
        all_current_batch_completed: Флаг завершения текущей партии.
        can_generate_next: Флаг доступности генерации следующей партии.
        completed_batches: Завершённые партии.
        work_ready_batch: Партия для работы.
        work_href: Ссылка на работу.
    """

    model_config = ConfigDict(frozen=True)

    track: str
    title: str
    subtitle: str
    card: TrackCardDTO
    batch_cards: list[TrackCardDTO]
    current_batch: int
    completed_total: int
    generated_total: int
    all_current_batch_completed: bool
    can_generate_next: bool
    completed_batches: int
    work_ready_batch: int | None = None
    work_href: str | None = None


class CardCompletionResultDTO(BaseModel):
    """Результат завершения карточки.

    Атрибуты:
        card_id: Идентификатор карточки.
        track: Ключ трека.
        batch_completed: Флаг завершения всей партии.
    """

    model_config = ConfigDict(frozen=True)

    card_id: int
    track: str
    batch_completed: bool


class GeneratedCardDraftDTO(BaseModel):
    """Черновик карточки, сгенерированный нейросетью.

    Атрибуты:
        topic: Тема карточки.
        explanation: Объяснение темы.
        examples: Примеры употребления.
        key_terms: Ключевые термины.
    """

    model_config = ConfigDict(frozen=True)

    topic: str
    explanation: str
    examples: list[str]
    key_terms: list[str]
