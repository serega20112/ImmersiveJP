from __future__ import annotations

from src.application.dto.learning import PdfDocumentDTO
from src.application.exceptions import NoCompletedCardsError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import PdfBuilder
from src.application.use_cases.mappers import to_track_card_dto
from src.domain.value_objects.track_type import TrackType


class ExportCardsToPDFUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        pdf_builder: PdfBuilder,
    ):
        """Initialize the export cards to PDF use case.

        Args:
            uow: Unit of work for database transactions.
            pdf_builder: Service for building PDF documents.
        """
        self._uow = uow
        self._pdf_builder = pdf_builder

    async def execute(self, user_id: int, track: TrackType) -> PdfDocumentDTO:
        """Export completed cards to a PDF document.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The PDF document data.

        Raises:
            NoCompletedCardsError: If no completed cards are available.
        """
        async with self._uow as uow:
            user_repository = uow.repository("user")
            content_repository = uow.repository("content")
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise NoCompletedCardsError("Пользователь не найден")
            cards = await content_repository.list_completed_cards(user_id, track)
            if not cards:
                raise NoCompletedCardsError("Пока нет завершенных карточек для экспорта")
        card_dtos = [
            to_track_card_dto(card, {int(card.id)} if card.id is not None else set())
            for card in cards
        ]
        pdf_bytes = await self._pdf_builder.build_cards_pdf(
            user_display_name=str(user.display_name),
            track=track,
            cards=card_dtos,
        )
        return PdfDocumentDTO(
            filename=f"immersjp-{track.value}-notes.pdf",
            content=pdf_bytes,
        )
