"""DTO речевой практики: слова, фразы, диалоги."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SpeechLineDTO(BaseModel):
    """Одна фраза для речевой практики.

    Атрибуты:
        japanese: Фраза на японском.
        romaji: Транслитерация.
        translation: Перевод фразы.
    """

    model_config = ConfigDict(frozen=True)

    japanese: str
    romaji: str | None = None
    translation: str | None = None


class SpeechDialogueTurnDTO(BaseModel):
    """Реплика в диалоге для речевой практики.

    Атрибуты:
        speaker: Имя говорящего.
        japanese: Реплика на японском.
        romaji: Транслитерация.
        translation: Перевод реплики.
    """

    model_config = ConfigDict(frozen=True)

    speaker: str
    japanese: str
    romaji: str | None = None
    translation: str | None = None


class SpeechDialogueDTO(BaseModel):
    """Диалог для речевой практики.

    Атрибуты:
        title: Название диалога.
        scenario: Описание сценария.
        turns: Реплики диалога.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    scenario: str
    turns: list[SpeechDialogueTurnDTO] = Field(default_factory=list)


class SpeechPracticeDTO(BaseModel):
    """Сгенерированный набор упражнений на произношение.

    Атрибуты:
        words: Слова для отработки.
        sentences: Фразы для отработки.
        dialogues: Диалоги для отработки.
        coaching_tip: Совет по произношению.
        difficulty_label: Название уровня сложности.
    """

    model_config = ConfigDict(frozen=True)

    words: list[str] = Field(default_factory=list)
    sentences: list[SpeechLineDTO] = Field(default_factory=list)
    dialogues: list[SpeechDialogueDTO] = Field(default_factory=list)
    coaching_tip: str
    difficulty_label: str


class SpeechPracticePageDTO(BaseModel):
    """Страница речевой практики.

    Атрибуты:
        title: Заголовок страницы.
        subtitle: Подзаголовок страницы.
        words_text: Исходный список слов текстом.
        suggested_words: Подсказанные слова.
        latest_topics: Последние темы.
        skill_summary: Резюме оценки навыков.
        practice: Сгенерированные упражнения.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    words_text: str
    suggested_words: list[str] = Field(default_factory=list)
    latest_topics: list[str] = Field(default_factory=list)
    skill_summary: str | None = None
    practice: SpeechPracticeDTO | None = None
