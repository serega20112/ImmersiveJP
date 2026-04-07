from __future__ import annotations

from src.backend.dto.profile_dto import AIAdviceDTO, LearningPlanPageDTO, ProgressReportDTO
from src.backend.use_case.profile import (
    BuildLearningPlanUseCase,
    BuildProgressReportUseCase,
    GenerateAIAdviceUseCase,
)


class ProfileService:
    def __init__(
        self,
        build_learning_plan_use_case: BuildLearningPlanUseCase,
        build_progress_report_use_case: BuildProgressReportUseCase,
        generate_ai_advice_use_case: GenerateAIAdviceUseCase,
    ):
        self._build_learning_plan_use_case = build_learning_plan_use_case
        self._build_progress_report_use_case = build_progress_report_use_case
        self._generate_ai_advice_use_case = generate_ai_advice_use_case

    async def build_learning_plan(self, user_id: int) -> LearningPlanPageDTO:
        return await self._build_learning_plan_use_case.execute(user_id)

    async def build_progress_report(self, user_id: int) -> ProgressReportDTO:
        return await self._build_progress_report_use_case.execute(user_id)

    async def generate_ai_advice(
        self,
        user_id: int,
        report: ProgressReportDTO,
    ) -> AIAdviceDTO:
        return await self._generate_ai_advice_use_case.execute(user_id, report)
