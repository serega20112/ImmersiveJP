from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import TrackPageDTO
from src.backend.infrastructure.repositories import (
    AbstractProgressRepository,
    AbstractSessionRepository,
)
from src.backend.use_case.learning.generate_cards import GenerateCardsUseCase
from src.backend.use_case.learning.get_track_page import GetTrackPageUseCase


class CurrentBatchNotCompletedError(Exception):
    pass


class GetNextCardsUseCase:
    def __init__(
        self,
        session_repository: AbstractSessionRepository,
        progress_repository: AbstractProgressRepository,
        generate_cards_use_case: GenerateCardsUseCase,
        get_track_page_use_case: GetTrackPageUseCase,
    ):
        self._session_repository = session_repository
        self._progress_repository = progress_repository
        self._generate_cards_use_case = generate_cards_use_case
        self._get_track_page_use_case = get_track_page_use_case

    async def execute(self, user_id: int, track: TrackType) -> TrackPageDTO:
        session = await self._session_repository.get_track_session(user_id, track)
        if session is not None and session.last_generated_batch > 0:
            is_completed = await self._progress_repository.is_batch_completed(
                user_id,
                track,
                session.last_generated_batch,
            )
            if not is_completed:
                raise CurrentBatchNotCompletedError(
                    "Сначала закрой текущую партию карточек"
                )
        await self._generate_cards_use_case.execute(user_id, track)
        return await self._get_track_page_use_case.execute(user_id, track)
