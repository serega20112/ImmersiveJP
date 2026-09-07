"""Схемы форм и запросов обучения."""

from __future__ import annotations

from fastapi import Form, Query
from pydantic import BaseModel


class CompleteCardForm(BaseModel):
    """Форма отметки карточки как пройденной.

    Атрибуты:
        card_id: Идентификатор карточки.
        track: Ключ трека обучения.
        return_to: Адрес возврата после завершения.
    """

    card_id: int = Form()
    track: str = Form()
    return_to: str | None = Form(None)


class SpeechPracticeForm(BaseModel):
    """Форма генерации речевой практики.

    Атрибуты:
        words_text: Слова для отработки, через запятую или перевод строки.
    """

    words_text: str = Form()


class TrackQuery(BaseModel):
    """Query-параметры трека обучения.

    Атрибуты:
        track: Ключ трека обучения.
    """

    track: str = Query()
