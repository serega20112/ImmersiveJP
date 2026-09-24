from __future__ import annotations

from src.application.dto.learning import CardBatchStatusDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.mappers import to_track_card_dto
from src.domain.entities.progress import CARD_BATCH_SIZE
from src.domain.value_objects import BatchGenerationState, TrackType


class GetCardBatchStatusUseCase:
    """Вернуть состояние партии и уже записанные карточки для опроса страницы."""

    def __init__(self, uow: UnitOfWork):
        """Инициализировать юзкейс статуса партии.

        Args:
            uow: Единица работы с базой.
        """
        self._uow = uow

    async def execute(self, user_id: int, track: TrackType) -> CardBatchStatusDTO:
        """Собрать статус текущей партии.

        Завершённые карточки отдаются вместе с карточками: фрагмент подменяет
        список целиком, и без отметок пройденные карточки визуально сбросились
        бы обратно в «не пройдено» на глазах у пользователя.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.

        Returns:
            Статус партии с уже записанными карточками.
        """
        async with self._uow as uow:
            session_repository = uow.repository("session")
            content_repository = uow.repository("content")
            progress_repository = uow.repository("progress")
            session = await session_repository.get_track_session(user_id, track)
            batch_number = session.last_generated_batch if session is not None else 0
            cards = []
            if batch_number > 0:
                cards = await content_repository.list_cards_by_batch(user_id, track, batch_number)
            completed_ids = set(
                await progress_repository.list_completed_card_ids(
                    user_id,
                    [int(card.id or 0) for card in cards],
                )
            )
        state = session.generation_state if session is not None else BatchGenerationState.READY
        return CardBatchStatusDTO(
            state=state.value,
            is_generating=state is BatchGenerationState.GENERATING,
            is_failed=state is BatchGenerationState.FAILED,
            batch_number=batch_number,
            expected_cards=CARD_BATCH_SIZE,
            cards=[to_track_card_dto(card, completed_ids) for card in cards],
        )
