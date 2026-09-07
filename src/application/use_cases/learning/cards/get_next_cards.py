from __future__ import annotations

from src.application.dto.learning import TrackPageDTO
from src.application.exceptions import CurrentBatchNotCompletedError
from src.application.interfaces import UnitOfWork
from src.application.use_cases.learning.cards.generate_cards import GenerateCardsUseCase
from src.application.use_cases.learning.cards.get_track_page import GetTrackPageUseCase
from src.domain.value_objects.track_type import TrackType


class GetNextCardsUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        generate_cards_use_case: GenerateCardsUseCase,
        get_track_page_use_case: GetTrackPageUseCase,
    ):
        """Initialize the get next cards use case.

        Args:
            uow: Unit of work for database transactions.
            generate_cards_use_case: Use case for generating cards.
            get_track_page_use_case: Use case for getting the track page.
        """
        self._uow = uow
        self._generate_cards_use_case = generate_cards_use_case
        self._get_track_page_use_case = get_track_page_use_case

    async def execute(self, user_id: int, track: TrackType) -> TrackPageDTO:
        """Generate the next batch of cards and return the track page.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The updated track page data.

        Raises:
            CurrentBatchNotCompletedError: If the current batch is not completed.
        """
        async with self._uow as uow:
            session_repository = uow.repository("session")
            progress_repository = uow.repository("progress")
            session = await session_repository.get_track_session(user_id, track)
            if session is not None and session.last_generated_batch > 0:
                is_completed = await progress_repository.is_batch_completed(
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
