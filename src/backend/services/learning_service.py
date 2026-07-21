from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import (
    CardCompletionResultDTO,
    PdfDocumentDTO,
    SpeechPracticePageDTO,
    TrackCardPageDTO,
    TrackPageDTO,
    TrackWorkPageDTO,
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
        """Initialize the learning service.

        Args:
            get_track_page_use_case: Use case for getting a track page.
            get_card_page_use_case: Use case for getting a card page.
            repair_current_batch_use_case: Use case for repairing the current batch.
            complete_card_use_case: Use case for completing a card.
            get_next_cards_use_case: Use case for getting the next cards.
            export_cards_to_pdf_use_case: Use case for exporting cards to PDF.
            get_speech_practice_page_use_case: Use case for getting speech practice page.
            generate_speech_practice_use_case: Use case for generating speech practice.
            get_track_work_page_use_case: Use case for getting track work page.
            submit_track_work_use_case: Use case for submitting track work.
        """
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
        """Get the track page after repairing the current batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The track page data.
        """
        await self._repair_current_batch_use_case.execute(user_id, track)
        return await self._get_track_page_use_case.execute(user_id, track)

    async def get_card_page(
        self,
        user_id: int,
        track: TrackType,
        card_id: int,
    ) -> TrackCardPageDTO:
        """Get the card page after repairing the current batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            card_id: ID of the card.

        Returns:
            The track card page data.
        """
        await self._repair_current_batch_use_case.execute(user_id, track)
        return await self._get_card_page_use_case.execute(user_id, track, card_id)

    async def complete_card(self, user_id: int, card_id: int) -> CardCompletionResultDTO:
        """Mark a card as completed.

        Args:
            user_id: ID of the user.
            card_id: ID of the card to complete.

        Returns:
            The card completion result.
        """
        return await self._complete_card_use_case.execute(user_id, card_id)

    async def get_next_cards(self, user_id: int, track: TrackType) -> TrackPageDTO:
        """Get the next batch of cards for a track.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The updated track page data.
        """
        return await self._get_next_cards_use_case.execute(user_id, track)

    async def export_cards_to_pdf(self, user_id: int, track: TrackType) -> PdfDocumentDTO:
        """Export completed cards to a PDF document.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The PDF document data.
        """
        return await self._export_cards_to_pdf_use_case.execute(user_id, track)

    async def get_speech_practice_page(self, user_id: int) -> SpeechPracticePageDTO:
        """Get the speech practice page.

        Args:
            user_id: ID of the user.

        Returns:
            The speech practice page data.
        """
        return await self._get_speech_practice_page_use_case.execute(user_id)

    async def generate_speech_practice(
        self,
        user_id: int,
        words_text: str,
    ) -> SpeechPracticePageDTO:
        """Generate speech practice content for given words.

        Args:
            user_id: ID of the user.
            words_text: Comma or newline separated words.

        Returns:
            The generated speech practice page data.
        """
        return await self._generate_speech_practice_use_case.execute(user_id, words_text)

    async def get_track_work_page(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> TrackWorkPageDTO:
        """Get the track work page for a specific batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.

        Returns:
            The track work page data.
        """
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
        """Submit answers for a track work batch.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: The batch number.
            answers: Dictionary of task ID to answer text.

        Returns:
            The track work page with results.
        """
        return await self._submit_track_work_use_case.execute(
            user_id,
            track,
            batch_number,
            answers,
        )
