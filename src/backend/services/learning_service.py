from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import (
    CardCompletionResultDTO,
    PdfDocumentDTO,
    TrackPageDTO,
)
from src.backend.use_case.learning import (
    CompleteCardUseCase,
    ExportCardsToPDFUseCase,
    GetNextCardsUseCase,
    GetTrackPageUseCase,
)


class LearningService:
    def __init__(
        self,
        get_track_page_use_case: GetTrackPageUseCase,
        complete_card_use_case: CompleteCardUseCase,
        get_next_cards_use_case: GetNextCardsUseCase,
        export_cards_to_pdf_use_case: ExportCardsToPDFUseCase,
    ):
        self._get_track_page_use_case = get_track_page_use_case
        self._complete_card_use_case = complete_card_use_case
        self._get_next_cards_use_case = get_next_cards_use_case
        self._export_cards_to_pdf_use_case = export_cards_to_pdf_use_case

    async def get_track_page(self, user_id: int, track: TrackType) -> TrackPageDTO:
        return await self._get_track_page_use_case.execute(user_id, track)

    async def complete_card(
        self, user_id: int, card_id: int
    ) -> CardCompletionResultDTO:
        return await self._complete_card_use_case.execute(user_id, card_id)

    async def get_next_cards(self, user_id: int, track: TrackType) -> TrackPageDTO:
        return await self._get_next_cards_use_case.execute(user_id, track)

    async def export_cards_to_pdf(
        self, user_id: int, track: TrackType
    ) -> PdfDocumentDTO:
        return await self._export_cards_to_pdf_use_case.execute(user_id, track)
