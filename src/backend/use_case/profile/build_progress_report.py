from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.domain.progress import TrackProgressSnapshot
from src.backend.dto.profile_dto import ProgressReportDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractProgressRepository,
    AbstractSessionRepository,
)
from src.backend.use_case.mappers import to_track_progress_dto


class BuildProgressReportUseCase:
    def __init__(
        self,
        content_repository: AbstractContentRepository,
        progress_repository: AbstractProgressRepository,
        session_repository: AbstractSessionRepository,
    ):
        self._content_repository = content_repository
        self._progress_repository = progress_repository
        self._session_repository = session_repository

    async def execute(self, user_id: int) -> ProgressReportDTO:
        snapshots: list[TrackProgressSnapshot] = []
        total_generated = 0
        total_completed = await self._progress_repository.get_total_completed(user_id)
        for track in TrackType:
            session = await self._session_repository.get_track_session(user_id, track)
            generated_cards = await self._content_repository.count_cards(user_id, track)
            completed_cards = await self._progress_repository.get_completed_count(
                user_id, track
            )
            snapshot = TrackProgressSnapshot(
                track=track,
                completed_cards=completed_cards,
                generated_cards=generated_cards,
                current_batch=session.last_generated_batch if session else 0,
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
        return ProgressReportDTO(
            total_completed=total_completed,
            total_generated=total_generated,
            completion_rate=completion_rate,
            next_step=(
                f"Добей текущую партию в блоке '{next_track.track.title}' и только потом запускай следующую."
                if total_generated
                else "Пройди онбординг, чтобы получить первую партию карточек."
            ),
            tracks=[to_track_progress_dto(snapshot) for snapshot in snapshots],
        )
