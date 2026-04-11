from __future__ import annotations

from typing import Protocol

from src.backend.domain.content import TrackType
from src.backend.dto.auth_dto import (
    AuthResultDTO,
    LoginDTO,
    RegistrationDTO,
    UserViewDTO,
    VerificationDTO,
)
from src.backend.dto.learning_dto import (
    CardCompletionResultDTO,
    PdfDocumentDTO,
    SpeechPracticePageDTO,
    TrackCardPageDTO,
    TrackPageDTO,
    TrackWorkPageDTO,
)
from src.backend.dto.mentor_dto import MentorPageDTO
from src.backend.dto.onboarding_dto import (
    OnboardingDTO,
    OnboardingPageDTO,
    OnboardingResultDTO,
)
from src.backend.dto.profile_dto import AIAdviceDTO, DashboardDTO, LearningPlanPageDTO, ProgressReportDTO


class AuthServiceContract(Protocol):
    async def register(self, payload: RegistrationDTO) -> UserViewDTO: ...

    async def verify_email(self, payload: VerificationDTO) -> UserViewDTO: ...

    async def login(self, payload: LoginDTO) -> AuthResultDTO: ...

    async def logout(self, access_token: str | None, refresh_token: str | None) -> None: ...

    async def resolve_current_user(self, access_token: str | None) -> UserViewDTO | None: ...


class DashboardServiceContract(Protocol):
    async def get_dashboard(self, user_id: int) -> DashboardDTO: ...


class LearningServiceContract(Protocol):
    async def get_track_page(self, user_id: int, track: TrackType) -> TrackPageDTO: ...

    async def get_card_page(
        self,
        user_id: int,
        track: TrackType,
        card_id: int,
    ) -> TrackCardPageDTO: ...

    async def complete_card(self, user_id: int, card_id: int) -> CardCompletionResultDTO: ...

    async def get_next_cards(self, user_id: int, track: TrackType) -> TrackPageDTO: ...

    async def export_cards_to_pdf(self, user_id: int, track: TrackType) -> PdfDocumentDTO: ...

    async def get_speech_practice_page(self, user_id: int) -> SpeechPracticePageDTO: ...

    async def generate_speech_practice(
        self,
        user_id: int,
        words_text: str,
    ) -> SpeechPracticePageDTO: ...

    async def get_track_work_page(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> TrackWorkPageDTO: ...

    async def submit_track_work(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        answers: dict[str, str],
    ) -> TrackWorkPageDTO: ...


class OnboardingServiceContract(Protocol):
    async def get_page(self) -> OnboardingPageDTO: ...

    async def complete(self, user_id: int, payload: OnboardingDTO) -> OnboardingResultDTO: ...


class ProfileServiceContract(Protocol):
    async def build_learning_plan(self, user_id: int) -> LearningPlanPageDTO: ...

    async def build_progress_report(self, user_id: int) -> ProgressReportDTO: ...

    async def generate_ai_advice(
        self,
        user_id: int,
        report: ProgressReportDTO,
    ) -> AIAdviceDTO: ...

    async def get_mentor_page(self, user_id: int) -> MentorPageDTO: ...

    async def send_mentor_message(self, user_id: int, message_text: str) -> MentorPageDTO: ...
