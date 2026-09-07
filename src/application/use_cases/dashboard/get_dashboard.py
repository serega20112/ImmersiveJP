from __future__ import annotations

from src.application.dto.profile import DashboardDTO, DashboardSectionDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.mappers import to_skill_assessment_dto
from src.application.use_cases.profile.build_progress_report import (
    BuildProgressReportUseCase,
)


class GetDashboardUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        build_progress_report_use_case: BuildProgressReportUseCase,
    ):
        """Initialize the get dashboard use case.

        Args:
            uow: Unit of work for database transactions.
            build_progress_report_use_case: Use case for building progress reports.
        """
        self._uow = uow
        self._build_progress_report_use_case = build_progress_report_use_case

    async def execute(self, user_id: int) -> DashboardDTO:
        """Build the dashboard for a user.

        Args:
            user_id: ID of the user.

        Returns:
            The dashboard data.

        Raises:
            ValueError: If the user is not found.
        """
        async with self._uow as uow:
            user_repository = uow.repository("user")
            user = await user_repository.get_by_id(user_id)
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
                completed_batches=item.completed_batches,
                work_ready_batch=item.work_ready_batch,
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
            user_display_name=str(user.display_name),
            recommendation=recommendation,
            sections=sections,
            trust_score=report.trust_score,
            skill_assessment=to_skill_assessment_dto(user.skill_assessment),
            speech_practice_href="/learn/speech",
        )

    @staticmethod
    def _subtitle_for_track(track: str) -> str:
        """Get the subtitle for a track name.

        Args:
            track: The track key.

        Returns:
            The track subtitle.
        """
        subtitles = {
            "language": "Фразы, грамматика и примеры",
            "culture": "Быт, нормы и повседневные сцены",
            "history": "Периоды, события и последствия",
        }
        return subtitles[track]
