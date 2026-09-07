from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.domain.value_objects import CardCount, CompletionRate, TrackType

CARD_BATCH_SIZE = 5


@dataclass
class TrackProgressSnapshot:
    """Снимок прогресса пользователя по треку."""

    BATCH_SIZE: ClassVar[int] = CARD_BATCH_SIZE

    track: TrackType
    completed_cards: CardCount
    generated_cards: CardCount
    current_batch: int
    completed_batches: int = 0
    work_ready_batch: int | None = None

    @property
    def completion_rate(self) -> CompletionRate:
        """Вычисляет процент завершения трека."""
        if self.generated_cards.value == 0:
            return CompletionRate(0.0)
        percentage = (self.completed_cards.value / self.generated_cards.value) * 100
        return CompletionRate(percentage)

    def advance_batch(self) -> None:
        """Переходит к следующему батчу."""
        self.current_batch += 1
        self.completed_batches += 1

    def mark_work_ready(self) -> None:
        """Отмечает текущий батч как готовый к проверке."""
        self.work_ready_batch = self.current_batch
