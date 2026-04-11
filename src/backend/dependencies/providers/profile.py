from __future__ import annotations

from functools import cached_property

from src.backend.services import DashboardService, ProfileService
from src.backend.use_case.dashboard import GetDashboardUseCase
from src.backend.use_case.profile import (
    BuildLearningPlanUseCase,
    BuildProgressReportUseCase,
    GenerateAIAdviceUseCase,
    GetMentorPageUseCase,
    SendMentorMessageUseCase,
)


class ProfileProvidersMixin:
    @cached_property
    def build_progress_report_use_case(self) -> BuildProgressReportUseCase:
        return BuildProgressReportUseCase(
            self.content_repository,
            self.progress_repository,
            self.session_repository,
            self.user_repository,
        )

    @cached_property
    def build_learning_plan_use_case(self) -> BuildLearningPlanUseCase:
        return BuildLearningPlanUseCase(
            self.user_repository,
            self.build_progress_report_use_case,
        )

    @cached_property
    def get_mentor_page_use_case(self) -> GetMentorPageUseCase:
        return GetMentorPageUseCase(
            self.mentor_repository,
            self.build_progress_report_use_case,
            self.build_learning_plan_use_case,
        )

    @cached_property
    def send_mentor_message_use_case(self) -> SendMentorMessageUseCase:
        return SendMentorMessageUseCase(
            self.user_repository,
            self.mentor_repository,
            self.build_progress_report_use_case,
            self.build_learning_plan_use_case,
            self.get_mentor_page_use_case,
            self.root.llm_client,
        )

    @cached_property
    def generate_ai_advice_use_case(self) -> GenerateAIAdviceUseCase:
        return GenerateAIAdviceUseCase(self.user_repository, self.root.llm_client)

    @cached_property
    def get_dashboard_use_case(self) -> GetDashboardUseCase:
        return GetDashboardUseCase(
            self.user_repository,
            self.build_progress_report_use_case,
        )

    @cached_property
    def profile_service(self) -> ProfileService:
        return ProfileService(
            self.build_learning_plan_use_case,
            self.build_progress_report_use_case,
            self.generate_ai_advice_use_case,
            self.get_mentor_page_use_case,
            self.send_mentor_message_use_case,
        )

    @cached_property
    def dashboard_service(self) -> DashboardService:
        return DashboardService(self.get_dashboard_use_case)
