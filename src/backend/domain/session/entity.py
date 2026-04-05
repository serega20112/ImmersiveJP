from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.backend.domain.content.enums import TrackType


@dataclass(slots=True)
class LearningSession:
    user_id: int
    track: TrackType
    last_generated_batch: int
    id: int | None = None
    updated_at: datetime | None = None
