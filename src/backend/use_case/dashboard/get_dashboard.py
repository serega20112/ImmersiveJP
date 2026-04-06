from __future__ import annotations

from src.backend.dto.profile_dto import DashboardDTO, DashboardSectionDTO
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.mappers import to_skill_assessment_dto
from src.backend.use_case.profile.build_progress_report import (
    BuildProgressReportUseCase,
)


class GetDashboardUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        build_progress_report_use_case: BuildProgressReportUseCase,
    ):
        self._user_repository = user_repository
        self._build_progress_report_use_case = build_progress_report_use_case

    async def execute(self, user_id: int) -> DashboardDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        report = await self._build_progress_report_use_case.execute(user_id)
        sections = [
            DashboardSectionDTO(
                track=item.track,
                title=item.title,
                subtitle=self._subtitle_for_track(item.track),
                completed_cards=item.completed_cards,
                generated_cards=item.generated_cards,
                completion_rate=item.completion_rate,
                href=f"/learn/{item.track}",
            )
            for item in report.tracks
        ]
        recommendation = (
            report.next_step
            if user.onboarding_completed
            else "Сначала пройди онбординг. После этого сервис подготовит стартовые карточки по трем разделам."
        )
        return DashboardDTO(
            user_display_name=user.display_name,
            recommendation=recommendation,
            sections=sections,
            skill_assessment=to_skill_assessment_dto(user.skill_assessment),
            speech_practice_href="/learn/speech",
        )

    @staticmethod
    def _subtitle_for_track(track: str) -> str:
        subtitles = {
            "language": "Фразы, грамматика и примеры",
            "culture": "Быт, нормы и повседневные сцены",
            "history": "Периоды, события и последствия",
        }
        return subtitles[track]
