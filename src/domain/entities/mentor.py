from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MentorMessage:
    """Сообщение от ментора."""

    role: str
    content: str
    created_at: datetime
    action_steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MentorFocus:
    """Фокус ментора для пользователя."""

    key: str
    title: str
    note: str
    track: str = "language"
