from __future__ import annotations

from dataclasses import dataclass

from src.backend.domain.content.enums import TrackType


@dataclass(slots=True)
class TrackProgressSnapshot:
    BATCH_SIZE = 10

    track: TrackType
    completed_cards: int
    generated_cards: int
    current_batch: int

    @property
    def completion_rate(self) -> float:
        if not self.generated_cards:
            return 0.0
        return round((self.completed_cards / self.generated_cards) * 100, 1)

    @property
    def completed_batches(self) -> int:
        return self.completed_cards // self.BATCH_SIZE

    @property
    def work_ready_batch(self) -> int | None:
        if self.completed_batches <= 0:
            return None
        return self.completed_batches
