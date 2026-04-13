from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.domain.progress import TrackProgressSnapshot
from src.backend.dto.profile_dto import ProgressReportDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
    AbstractSessionRepository,
    AbstractUserRepository,
)
from src.backend.use_case.batch_progress import summarize_completed_batches
from src.backend.use_case.mappers import to_skill_assessment_dto, to_track_progress_dto
from src.backend.use_case.profile.trust_score import build_trust_score


class BuildProgressReportUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
        session_repository: AbstractSessionRepository,
        user_repository: AbstractUserRepository,
    ):
        self._content_repository = content_repository
        self._progress_repository = progress_repository
        self._session_repository = session_repository
        self._user_repository = user_repository

    async def execute(self, user_id: int) -> ProgressReportDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        snapshots: list[TrackProgressSnapshot] = []
        total_generated = 0
        total_completed = await self._progress_repository.get_total_completed(user_id)
        for track in TrackType:
            session = await self._session_repository.get_track_session(user_id, track)
            current_batch = session.last_generated_batch if session else 0
            generated_cards = await self._content_repository.count_cards(user_id, track)
            completed_cards = await self._progress_repository.get_completed_count(
                user_id, track
            )
            completed_batches, work_ready_batch = await summarize_completed_batches(
                self._progress_repository,
                user_id=user_id,
                track=track,
                current_batch=current_batch,
            )
            snapshot = TrackProgressSnapshot(
                track=track,
                completed_cards=completed_cards,
                generated_cards=generated_cards,
                current_batch=current_batch,
                completed_batches=completed_batches,
                work_ready_batch=work_ready_batch,
            )
            snapshots.append(snapshot)
            total_generated += generated_cards

        next_track = min(
            snapshots,
            key=lambda item: item.completion_rate if item.generated_cards else -1,
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
