from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.backend.domain.content import LearningCard, TrackType
from src.backend.domain.progress import CARD_BATCH_SIZE
from src.backend.use_case.learning.get_card_page import GetCardPageUseCase


class _CardPageContentRepository:
    def __init__(self):
        self.cards = [
            LearningCard(
                id=index,
                user_id=42,
                track=TrackType.CULTURE,
                topic=f"Тема {index}",
                explanation="Короткое объяснение карточки.",
                examples=["文化 | bunka | культура"],
                key_terms=["文化"],
                batch_number=1,
                position=index,
            )
            for index in range(1, CARD_BATCH_SIZE + 1)
        ]

    async def get_by_id(self, card_id: int):
        for card in self.cards:
            if card.id == card_id:
                return card
        return None

    async def list_cards_by_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ):
        if user_id != 42 or track != TrackType.CULTURE or batch_number != 1:
            return []
        return self.cards

    async def count_cards(self, user_id: int, track: TrackType) -> int:
        if user_id != 42 or track != TrackType.CULTURE:
            return 0
        return len(self.cards)


class _CardPageProgressRepository:
    async def list_completed_card_ids(self, user_id: int, card_ids: list[int]):
        return list(card_ids)

    async def get_completed_count(self, user_id: int, track: TrackType) -> int:
        return CARD_BATCH_SIZE

    async def is_batch_completed(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> bool:
        return user_id == 42 and track == TrackType.CULTURE and batch_number == 1


class _CardPageSessionRepository:
    async def get_track_session(self, user_id: int, track: TrackType):
        if user_id != 42 or track != TrackType.CULTURE:
            return None
        return SimpleNamespace(last_generated_batch=1)


@pytest.mark.asyncio
async def test_card_page_unlocks_work_after_completed_five_card_batch():
    use_case = GetCardPageUseCase(
        _CardPageContentRepository(),
        _CardPageProgressRepository(),
        _CardPageSessionRepository(),
    )

    page = await use_case.execute(
        user_id=42,
        track=TrackType.CULTURE,
        card_id=1,
    )

    assert page.generated_total == CARD_BATCH_SIZE
    assert page.completed_total == CARD_BATCH_SIZE
    assert page.completed_batches == 1
    assert page.work_ready_batch == 1
    assert page.can_generate_next is True
