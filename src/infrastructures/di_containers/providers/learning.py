from __future__ import annotations

from functools import cached_property

from src.application.services import LearningService
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


class LearningProvidersMixin:
    @cached_property
    def start_batch_generation_use_case(self) -> StartCardBatchGenerationUseCase:
        return StartCardBatchGenerationUseCase(self.uow, self.root.rate_limiter)

    @cached_property
    def generate_cards_use_case(self) -> GenerateCardsUseCase:
        return GenerateCardsUseCase(
            self.uow,
            self.mentor_repository,
            self.root.llm_client,
        )

    @cached_property
    def get_card_batch_status_use_case(self) -> GetCardBatchStatusUseCase:
        return GetCardBatchStatusUseCase(self.uow)

    @cached_property
    def get_track_page_use_case(self) -> GetTrackPageUseCase:
        return GetTrackPageUseCase(self.uow)

    @cached_property
    def get_card_page_use_case(self) -> GetCardPageUseCase:
        return GetCardPageUseCase(self.uow)

    @cached_property
    def complete_card_use_case(self) -> CompleteCardUseCase:
        return CompleteCardUseCase(self.uow)

    @cached_property
    def export_cards_to_pdf_use_case(self) -> ExportCardsToPDFUseCase:
        return ExportCardsToPDFUseCase(self.uow, self.root.pdf_builder)

    @cached_property
    def get_speech_practice_page_use_case(self) -> GetSpeechPracticePageUseCase:
        return GetSpeechPracticePageUseCase(self.uow)

    @cached_property
    def generate_speech_practice_use_case(self) -> GenerateSpeechPracticeUseCase:
        return GenerateSpeechPracticeUseCase(
            self.uow,
            self.get_speech_practice_page_use_case,
            self.root.llm_client,
            self.root.rate_limiter,
        )

    @cached_property
    def get_track_work_page_use_case(self) -> GetTrackWorkPageUseCase:
        return GetTrackWorkPageUseCase(self.uow)

    @cached_property
    def submit_track_work_use_case(self) -> SubmitTrackWorkUseCase:
        return SubmitTrackWorkUseCase(self.uow, self.root.llm_client)

    @cached_property
    def learning_service(self) -> LearningService:
        return LearningService(
            self.get_track_page_use_case,
            self.get_card_page_use_case,
            self.complete_card_use_case,
            self.start_batch_generation_use_case,
            self.generate_cards_use_case,
            self.get_card_batch_status_use_case,
            self.export_cards_to_pdf_use_case,
            self.get_speech_practice_page_use_case,
            self.generate_speech_practice_use_case,
            self.get_track_work_page_use_case,
            self.submit_track_work_use_case,
        )
