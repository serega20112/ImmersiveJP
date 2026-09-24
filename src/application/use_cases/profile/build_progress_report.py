from __future__ import annotations

from src.application.dto.profile import ProgressReportDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.batch_progress import summarize_completed_batches
from src.application.use_cases.mappers import to_skill_assessment_dto, to_track_progress_dto
from src.application.use_cases.profile.trust_score import build_trust_score
from src.domain.entities.progress import TrackProgressSnapshot
from src.domain.value_objects import CardCount
from src.domain.value_objects.track_type import TrackType


class BuildProgressReportUseCase:
    def __init__(self, uow: UnitOfWork):
        """Initialize the build progress report use case.

        Args:
            uow: Unit of work for database transactions.
        """
        self._uow = uow

    async def execute(self, user_id: int) -> ProgressReportDTO:
        """Build a progress report for a user.

        Args:
            user_id: ID of the user.

        Returns:
            The progress report data.

        Raises:
            ValueError: If the user is not found.
        """
        async with self._uow as uow:
            content_repository = uow.learning_cards
            progress_repository = uow.progress
            session_repository = uow.sessions
            user_repository = uow.users
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            snapshots: list[TrackProgressSnapshot] = []
            total_generated = 0
            total_completed = await progress_repository.get_total_completed(user_id)
            for track in TrackType:
                session = await session_repository.get_track_session(user_id, track)
                current_batch = session.last_generated_batch if session else 0
                generated_cards = await content_repository.count_cards(user_id, track)
                completed_cards = await progress_repository.get_completed_count(
                    user_id,
                    track,
                )
                completed_batches, work_ready_batch = await summarize_completed_batches(
                    progress_repository,
                    user_id=user_id,
                    track=track,
                    current_batch=current_batch,
                )
                snapshot = TrackProgressSnapshot(
                    track=track,
                    completed_cards=CardCount(completed_cards),
                    generated_cards=CardCount(generated_cards),
                    current_batch=current_batch,
                    completed_batches=completed_batches,
                    work_ready_batch=work_ready_batch,
                )
                snapshots.append(snapshot)
                total_generated += generated_cards

            next_track = min(
                snapshots,
                key=lambda item: (
                    item.completion_rate.percentage if item.generated_cards.value else -1
                ),
            )
            completion_rate = (
                round((total_completed / total_generated) * 100, 1)
                if total_generated
                else 0.0
            )
            trust_score = build_trust_score(
                assessment=user.skill_assessment,
                snapshots=snapshots,
                total_completed=total_completed,
                total_generated=total_generated,
            )
            return ProgressReportDTO(
                total_completed=total_completed,
                total_generated=total_generated,
                completion_rate=completion_rate,
                next_step=(
                    f"Сейчас лучше закончить текущую партию в разделе '{next_track.track.title}'. После этого можно переходить дальше."
                    if total_generated
                    else "Сначала пройди онбординг, чтобы получить стартовые карточки."
                ),
                tracks=[to_track_progress_dto(snapshot) for snapshot in snapshots],
                trust_score=trust_score,
                skill_assessment=to_skill_assessment_dto(user.skill_assessment),
            )
