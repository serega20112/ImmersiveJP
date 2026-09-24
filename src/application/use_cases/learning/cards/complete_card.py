from __future__ import annotations

from src.application.dto.learning import CardCompletionResultDTO
from src.application.exceptions import CardOwnershipError
from src.application.interfaces import UnitOfWork


class CompleteCardUseCase:
    def __init__(self, uow: UnitOfWork):
        """Initialize the complete card use case.

        Args:
            uow: Unit of work for database transactions.
        """
        self._uow = uow

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
        async with self._uow as uow:
            content_repository = uow.learning_cards
            progress_repository = uow.progress
            card = await content_repository.get_by_id(card_id)
            if card is None or card.user_id != user_id:
                raise CardOwnershipError("Карточка не найдена")
            await progress_repository.complete_card(user_id, card_id)
            batch_completed = await progress_repository.is_batch_completed(
                user_id,
                card.track,
                int(card.batch_number),
            )
        return CardCompletionResultDTO(
            card_id=card_id,
            track=card.track.value,
            batch_completed=batch_completed,
        )
