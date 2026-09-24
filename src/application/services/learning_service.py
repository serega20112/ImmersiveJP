from __future__ import annotations

from src.application.dto.learning import (
    CardBatchStatusDTO,
    CardCompletionResultDTO,
    PdfDocumentDTO,
    SpeechPracticePageDTO,
    TrackCardPageDTO,
    TrackPageDTO,
    TrackWorkPageDTO,
)
from src.application.use_cases.learning import (
    CompleteCardUseCase,
    ExportCardsToPDFUseCase,
    GenerateCardsUseCase,
    GenerateSpeechPracticeUseCase,
    GetCardBatchStatusUseCase,
    GetCardPageUseCase,
    GetSpeechPracticePageUseCase,
    GetTrackPageUseCase,
    GetTrackWorkPageUseCase,
    StartCardBatchGenerationUseCase,
    SubmitTrackWorkUseCase,
)
from src.domain.value_objects.track_type import TrackType


class LearningService:
    def __init__(
        self,
        get_track_page_use_case: GetTrackPageUseCase,
        get_card_page_use_case: GetCardPageUseCase,
        complete_card_use_case: CompleteCardUseCase,
        start_batch_generation_use_case: StartCardBatchGenerationUseCase,
        generate_cards_use_case: GenerateCardsUseCase,
        get_card_batch_status_use_case: GetCardBatchStatusUseCase,
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
            complete_card_use_case: Use case for completing a card.
            start_batch_generation_use_case: Use case for reserving a card batch.
            generate_cards_use_case: Use case for writing a reserved batch.
            get_card_batch_status_use_case: Use case for polling batch status.
            export_cards_to_pdf_use_case: Use case for exporting cards to PDF.
            get_speech_practice_page_use_case: Use case for getting speech practice page.
            generate_speech_practice_use_case: Use case for generating speech practice.
            get_track_work_page_use_case: Use case for getting track work page.
            submit_track_work_use_case: Use case for submitting track work.
        """
        self._get_track_page_use_case = get_track_page_use_case
        self._get_card_page_use_case = get_card_page_use_case
        self._complete_card_use_case = complete_card_use_case
        self._start_batch_generation_use_case = start_batch_generation_use_case
        self._generate_cards_use_case = generate_cards_use_case
        self._get_card_batch_status_use_case = get_card_batch_status_use_case
        self._export_cards_to_pdf_use_case = export_cards_to_pdf_use_case
        self._get_speech_practice_page_use_case = get_speech_practice_page_use_case
        self._generate_speech_practice_use_case = generate_speech_practice_use_case
        self._get_track_work_page_use_case = get_track_work_page_use_case
        self._submit_track_work_use_case = submit_track_work_use_case

    async def get_track_page(self, user_id: int, track: TrackType) -> TrackPageDTO:
        """Get the track page.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            The track page data.
        """
        return await self._get_track_page_use_case.execute(user_id, track)

    async def get_card_page(
        self,
        user_id: int,
        track: TrackType,
        card_id: int,
    ) -> TrackCardPageDTO:
        """Get the card page.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            card_id: ID of the card.

        Returns:
            The track card page data.
        """
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

    async def start_batch_generation(self, user_id: int, track: TrackType) -> int:
        """Reserve the next card batch and return its number.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            Number of the batch the page should follow.
        """
        return await self._start_batch_generation_use_case.execute(user_id, track)

    async def generate_batch(self, user_id: int, track: TrackType, batch_number: int) -> None:
        """Write a reserved batch; runs detached from the request.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_number: Reserved batch number.
        """
        await self._generate_cards_use_case.execute(user_id, track, batch_number)

    async def get_batch_status(self, user_id: int, track: TrackType) -> CardBatchStatusDTO:
        """Get the current batch state and the cards already written.

        Args:
            user_id: ID of the user.
            track: The learning track type.

        Returns:
            Batch status data for the page poll.
        """
        return await self._get_card_batch_status_use_case.execute(user_id, track)

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
