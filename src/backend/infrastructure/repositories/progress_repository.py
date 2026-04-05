from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.domain.content import TrackType


class AbstractProgressRepository(ABC):
    @abstractmethod
    async def complete_card(self, user_id: int, card_id: int) -> None:
        pass

    @abstractmethod
    async def list_completed_card_ids(
        self, user_id: int, card_ids: list[int]
    ) -> list[int]:
        pass

    @abstractmethod
    async def get_completed_count(self, user_id: int, track: TrackType) -> int:
        pass

    @abstractmethod
    async def get_total_completed(self, user_id: int) -> int:
        pass

    @abstractmethod
    async def is_batch_completed(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> bool:
        pass
