from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.infrastructure.repositories import AbstractProgressRepository


async def summarize_completed_batches(
    progress_repository: AbstractProgressRepository,
    *,
    user_id: int,
    track: TrackType,
    current_batch: int,
) -> tuple[int, int | None]:
    if current_batch <= 0:
        return 0, None

    completed_batches = 0
    work_ready_batch: int | None = None
    for batch_number in range(1, current_batch + 1):
        if not await progress_repository.is_batch_completed(
            user_id,
            track,
            batch_number,
        ):
            continue
        completed_batches += 1
        work_ready_batch = batch_number
    return completed_batches, work_ready_batch
