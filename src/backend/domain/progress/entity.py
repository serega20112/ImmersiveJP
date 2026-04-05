from __future__ import annotations

from dataclasses import dataclass

from src.backend.domain.content.enums import TrackType


@dataclass(slots=True)
class TrackProgressSnapshot:
    track: TrackType
    completed_cards: int
    generated_cards: int
    current_batch: int

    @property
    def completion_rate(self) -> float:
        if not self.generated_cards:
            return 0.0
        return round((self.completed_cards / self.generated_cards) * 100, 1)
