from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.domain.content import TrackType
from src.backend.domain.session import LearningSession


class AbstractSessionRepository(ABC):
    @abstractmethod
    async def get_track_session(
        self,
        user_id: int,
        track: TrackType,
    ) -> LearningSession | None:
        pass

    @abstractmethod
    async def upsert_track_session(
        self,
        user_id: int,
        track: TrackType,
        last_generated_batch: int,
    ) -> LearningSession:
        pass
