from __future__ import annotations

from abc import ABC, abstractmethod

from src.backend.domain.content import LearningCard, TrackType


class AbstractContentRepository(ABC):
    @abstractmethod
    async def add_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        pass

    @abstractmethod
    async def update_many(self, cards: list[LearningCard]) -> list[LearningCard]:
        pass

    @abstractmethod
    async def get_by_id(self, card_id: int) -> LearningCard | None:
        pass

    @abstractmethod
    async def get_latest_batch_number(self, user_id: int, track: TrackType) -> int:
        pass

    @abstractmethod
    async def list_cards_by_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[LearningCard]:
        pass

    @abstractmethod
    async def list_recent_topics(
        self,
        user_id: int,
        track: TrackType,
        limit: int = 15,
    ) -> list[str]:
        pass

    @abstractmethod
    async def count_cards(self, user_id: int, track: TrackType) -> int:
        pass

    @abstractmethod
    async def list_completed_cards(
        self,
        user_id: int,
        track: TrackType,
    ) -> list[LearningCard]:
        pass

    @abstractmethod
    async def list_card_ids_for_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[int]:
        pass
