"""Схемы форм и ответов ментора."""

from __future__ import annotations

from fastapi import Form
from pydantic import BaseModel


class MentorMessageForm(BaseModel):
    """Форма отправки сообщения ментору.

    Атрибуты:
        message: Текст сообщения.
    """

    message: str = Form()


class VoiceInputResponse(BaseModel):
    """Ответ распознавания голосового ввода.

    Атрибуты:
        text: Распознанный текст.
    """

    text: str
