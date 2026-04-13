from __future__ import annotations

from functools import cached_property

from src.backend.services import LearningService
from src.backend.use_case.learning import (
    CompleteCardUseCase,
    ExportCardsToPDFUseCase,
    GenerateCardsUseCase,
    GenerateSpeechPracticeUseCase,
    GetCardPageUseCase,
    GetNextCardsUseCase,
    GetSpeechPracticePageUseCase,
    GetTrackPageUseCase,
    GetTrackWorkPageUseCase,
    RepairCurrentBatchUseCase,
    SubmitTrackWorkUseCase,
)


class LearningProvidersMixin:
    @cached_property
    def generate_cards_use_case(self) -> GenerateCardsUseCase:
        return GenerateCardsUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
            self.mentor_repository,
            self.root.llm_client,
            self.root.rate_limiter,
        )

    @cached_property
    def get_track_page_use_case(self) -> GetTrackPageUseCase:
        return GetTrackPageUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
        )

    @cached_property
    def get_card_page_use_case(self) -> GetCardPageUseCase:
        return GetCardPageUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
        )

    @cached_property
    def repair_current_batch_use_case(self) -> RepairCurrentBatchUseCase:
        return RepairCurrentBatchUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
            self.root.llm_client,
        )

    @cached_property
    def complete_card_use_case(self) -> CompleteCardUseCase:
        return CompleteCardUseCase(self.content_repository, self.progress_repository)

    @cached_property
    def get_next_cards_use_case(self) -> GetNextCardsUseCase:
        return GetNextCardsUseCase(
            self.session_repository,
            self.progress_repository,
            self.generate_cards_use_case,
            self.get_track_page_use_case,
        )

    @cached_property
    def export_cards_to_pdf_use_case(self) -> ExportCardsToPDFUseCase:
        return ExportCardsToPDFUseCase(
            self.user_repository,
            self.content_repository,
            self.root.pdf_builder,
        )

    @cached_property
    def get_speech_practice_page_use_case(self) -> GetSpeechPracticePageUseCase:
        return GetSpeechPracticePageUseCase(
            self.user_repository,
            self.content_repository,
            self.session_repository,
        )

    @cached_property
    def generate_speech_practice_use_case(self) -> GenerateSpeechPracticeUseCase:
        return GenerateSpeechPracticeUseCase(
            self.user_repository,
            self.get_speech_practice_page_use_case,
            self.root.llm_client,
            self.root.rate_limiter,
        )

    @cached_property
    def get_track_work_page_use_case(self) -> GetTrackWorkPageUseCase:
        return GetTrackWorkPageUseCase(
            self.content_repository,
            self.progress_repository,
        )

    @cached_property
    def submit_track_work_use_case(self) -> SubmitTrackWorkUseCase:
        return SubmitTrackWorkUseCase(
            self.user_repository,
            self.content_repository,
            self.progress_repository,
            self.root.llm_client,
        )

    @cached_property
    def learning_service(self) -> LearningService:
        return LearningService(
            self.get_track_page_use_case,
            self.get_card_page_use_case,
            self.repair_current_batch_use_case,
            self.complete_card_use_case,
            self.get_next_cards_use_case,
            self.export_cards_to_pdf_use_case,
            self.get_speech_practice_page_use_case,
            self.generate_speech_practice_use_case,
            self.get_track_work_page_use_case,
            self.submit_track_work_use_case,
        )
