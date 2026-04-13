from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.backend.domain.content.enums import TrackType

CARD_BATCH_SIZE = 5


@dataclass(slots=True)
class TrackProgressSnapshot:
    BATCH_SIZE: ClassVar[int] = CARD_BATCH_SIZE

    track: TrackType
    completed_cards: int
    generated_cards: int
    current_batch: int
    completed_batches: int = 0
    work_ready_batch: int | None = None

    @property
    def completion_rate(self) -> float:
        if not self.generated_cards:
            return 0.0
        return round((self.completed_cards / self.generated_cards) * 100, 1)
