from __future__ import annotations

from src.backend.dto.learning_dto import CardCompletionResultDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
)


class CardOwnershipError(Exception):
    pass


class CompleteCardUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
    ):
        """Initialize the complete card use case.

        Args:
            content_repository: Repository for content data.
            progress_repository: Repository for progress data.
        """
        self._content_repository = content_repository
        self._progress_repository = progress_repository

    async def execute(self, user_id: int, card_id: int) -> CardCompletionResultDTO:
        """Mark a card as completed by the user.

        Args:
            user_id: ID of the user.
            card_id: ID of the card to complete.

        Returns:
            The card completion result.

        Raises:
            CardOwnershipError: If the card does not belong to the user.
        """
        card = await self._content_repository.get_by_id(card_id)
        if card is None or card.user_id != user_id:
            raise CardOwnershipError("Карточка не найдена")
        await self._progress_repository.complete_card(user_id, card_id)
        batch_completed = await self._progress_repository.is_batch_completed(
            user_id,
            card.track,
            card.batch_number,
        )
        return CardCompletionResultDTO(
            card_id=card_id,
            track=card.track.value,
            batch_completed=batch_completed,
        )
