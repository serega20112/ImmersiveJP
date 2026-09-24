"""Схемы форм проверки знаний."""

from __future__ import annotations

from fastapi import Form
from pydantic import BaseModel


class KnowledgeGenerateForm(BaseModel):
    """Форма генерации вопросов для проверки.

    Атрибуты:
        focus_area: Необязательная область фокуса для вопросов.
    """

    focus_area: str = Form("")


class KnowledgeSubmitForm(BaseModel):
    """Форма отправки ответов проверки.

    Атрибуты:
        questions_json: JSON-строка с вопросами (скрытое поле формы).
    """

    questions_json: str = Form()
