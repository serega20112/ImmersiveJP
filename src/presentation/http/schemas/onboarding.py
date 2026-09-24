"""Схемы форм онбординга."""

from __future__ import annotations

from fastapi import Form
from pydantic import BaseModel


class OnboardingForm(BaseModel):
    """Форма онбординга.

    Атрибуты:
        goal: Цель обучения.
        language_level: Текущий уровень языка.
        study_timeline: Желаемый срок обучения.
        interests_text: Свободный текст интересов.
        diagnostic_hints_used: Количество использованных подсказок.
    """

    goal: str = Form("")
    language_level: str = Form("")
    study_timeline: str = Form("")
    interests_text: str = Form("")
    diagnostic_hints_used: int = Form(0)
