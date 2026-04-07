from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import (
    CardCompletionResultDTO,
    PdfDocumentDTO,
    SpeechPracticePageDTO,
    TrackWorkPageDTO,
    TrackCardPageDTO,
    TrackPageDTO,
)
from src.backend.use_case.learning import (
    CompleteCardUseCase,
    ExportCardsToPDFUseCase,
    GenerateSpeechPracticeUseCase,
    GetCardPageUseCase,
    GetNextCardsUseCase,
    GetSpeechPracticePageUseCase,
    GetTrackPageUseCase,
    GetTrackWorkPageUseCase,
    RepairCurrentBatchUseCase,
    SubmitTrackWorkUseCase,
)


class LearningService:
    def __init__(
        self,
        get_track_page_use_case: GetTrackPageUseCase,
        get_card_page_use_case: GetCardPageUseCase,
        repair_current_batch_use_case: RepairCurrentBatchUseCase,
        complete_card_use_case: CompleteCardUseCase,
        get_next_cards_use_case: GetNextCardsUseCase,
        export_cards_to_pdf_use_case: ExportCardsToPDFUseCase,
        get_speech_practice_page_use_case: GetSpeechPracticePageUseCase,
        generate_speech_practice_use_case: GenerateSpeechPracticeUseCase,
        get_track_work_page_use_case: GetTrackWorkPageUseCase,
        submit_track_work_use_case: SubmitTrackWorkUseCase,
    ):
        self._get_track_page_use_case = get_track_page_use_case
        self._get_card_page_use_case = get_card_page_use_case
        self._repair_current_batch_use_case = repair_current_batch_use_case
        self._complete_card_use_case = complete_card_use_case
        self._get_next_cards_use_case = get_next_cards_use_case
        self._export_cards_to_pdf_use_case = export_cards_to_pdf_use_case
        self._get_speech_practice_page_use_case = get_speech_practice_page_use_case
        self._generate_speech_practice_use_case = generate_speech_practice_use_case
        self._get_track_work_page_use_case = get_track_work_page_use_case
        self._submit_track_work_use_case = submit_track_work_use_case

    async def get_track_page(self, user_id: int, track: TrackType) -> TrackPageDTO:
        await self._repair_current_batch_use_case.execute(user_id, track)
        return await self._get_track_page_use_case.execute(user_id, track)

    async def get_card_page(
        self,
        user_id: int,
        track: TrackType,
        card_id: int,
    ) -> TrackCardPageDTO:
        await self._repair_current_batch_use_case.execute(user_id, track)
        return await self._get_card_page_use_case.execute(user_id, track, card_id)

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

    async def get_speech_practice_page(self, user_id: int) -> SpeechPracticePageDTO:
        return await self._get_speech_practice_page_use_case.execute(user_id)

    async def generate_speech_practice(
        self,
        user_id: int,
        words_text: str,
    ) -> SpeechPracticePageDTO:
        return await self._generate_speech_practice_use_case.execute(user_id, words_text)

    async def get_track_work_page(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> TrackWorkPageDTO:
        return await self._get_track_work_page_use_case.execute(
            user_id,
            track,
            batch_number,
        )

    async def submit_track_work(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        answers: dict[str, str],
    ) -> TrackWorkPageDTO:
        return await self._submit_track_work_use_case.execute(
            user_id,
            track,
            batch_number,
            answers,
        )
