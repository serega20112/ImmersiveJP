from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.backend.domain.content.enums import TrackType


@dataclass(slots=True)
class LearningCard:
    user_id: int
    track: TrackType
    topic: str
    explanation: str
    examples: list[str] = field(default_factory=list)
    key_terms: list[str] = field(default_factory=list)
    batch_number: int = 1
    position: int = 1
    id: int | None = None
    created_at: datetime | None = None
