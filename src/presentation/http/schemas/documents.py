"""Схемы форм документов пользователя."""

from __future__ import annotations

from fastapi import Form
from pydantic import BaseModel


class DocumentAddForm(BaseModel):
    """Форма добавления документа.

    Атрибуты:
        title: Заголовок документа.
        content: Текст документа.
    """

    title: str = Form()
    content: str = Form()
