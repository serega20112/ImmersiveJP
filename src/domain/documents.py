"""Доменная сущность пользовательского документа."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class UserDocument:
    """Пользовательский конспект: заголовок и текстовое содержимое."""

    id: int | None
    user_id: int
    title: str
    content: str
    created_at: datetime | None = None
