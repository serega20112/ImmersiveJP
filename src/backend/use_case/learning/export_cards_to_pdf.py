from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import PdfDocumentDTO
from src.backend.infrastructure.external import PdfBuilder
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractUserRepository,
)
from src.backend.use_case.mappers import to_track_card_dto


class NoCompletedCardsError(Exception):
    pass


class ExportCardsToPDFUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        content_repository: AbstractContentRepository,
        pdf_builder: PdfBuilder,
    ):
        self._user_repository = user_repository
        self._content_repository = content_repository
        self._pdf_builder = pdf_builder

    async def execute(self, user_id: int, track: TrackType) -> PdfDocumentDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise NoCompletedCardsError("Пользователь не найден")
        cards = await self._content_repository.list_completed_cards(user_id, track)
        if not cards:
            raise NoCompletedCardsError("Пока нет завершенных карточек для экспорта")
        card_dtos = [to_track_card_dto(card, {int(card.id or 0)}) for card in cards]
        pdf_bytes = await self._pdf_builder.build_cards_pdf(
            user_display_name=user.display_name,
            track=track,
            cards=card_dtos,
        )
        return PdfDocumentDTO(
            filename=f"immersjp-{track.value}-notes.pdf",
            content=pdf_bytes,
        )
