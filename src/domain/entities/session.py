from __future__ import annotations

from dataclasses import dataclass

from src.domain.value_objects import Timestamp, TrackType, UserID


@dataclass
class LearningSession:
    """Доменная модель учебной сессии."""

    user_id: UserID
    track: TrackType
    last_generated_batch: int
    updated_at: Timestamp

    @classmethod
    def create(cls, user_id: UserID, track: TrackType) -> LearningSession:
        """Создаёт новую учебную сессию.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.

        Returns:
            Новая учебная сессия.
        """
        timestamp = Timestamp.now()
        return cls(
            user_id=user_id,
            track=track,
            last_generated_batch=0,
            updated_at=timestamp,
        )

    def advance_batch(self) -> None:
        """Увеличивает номер последнего сгенерированного батча."""
        self.last_generated_batch += 1
        self.updated_at = self.updated_at.refresh()
