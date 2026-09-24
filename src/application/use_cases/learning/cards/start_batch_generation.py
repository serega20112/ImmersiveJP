from __future__ import annotations

import logging

from src.application.exceptions import (
    CurrentBatchNotCompletedError,
    LlmRateLimitExceededError,
)
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import RateLimiter
from src.config.settings import settings
from src.domain.entities import LearningSession
from src.domain.value_objects import TrackType, UserID
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class StartCardBatchGenerationUseCase:
    """Забронировать партию карточек и вернуть её номер.

    Работа намеренно не ждёт ответа модели: обращение к ней занимает секунды,
    а до этого запроса страница висела мёртвой. Здесь фиксируется только факт
    брони, а генерацией занимается фоновая задача.

    Атрибуты:
        _uow: Единица работы с базой.
        _rate_limiter: Ограничитель обращений к модели.
    """

    def __init__(self, uow: UnitOfWork, rate_limiter: RateLimiter):
        """Инициализировать юзкейс брони партии.

        Args:
            uow: Единица работы с базой.
            rate_limiter: Ограничитель обращений к модели.
        """
        self._uow = uow
        self._rate_limiter = rate_limiter

    async def execute(self, user_id: int, track: TrackType) -> int:
        """Забронировать партию либо вернуть уже бронируемую.

        Повторный вызов не должен порождать вторую платную генерацию: кнопка
        двойного клика, предзагрузка браузера и перезагрузка страницы попадают
        сюда повторно и обязаны получить ту же партию.

        Оборвавшуюся партию не пропускают: её дописывают под тем же номером, иначе
        половина партии осталась бы в базе мусором, а проверка завершённости
        заперла бы пользователя на месте.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.

        Returns:
            Номер партии, за которой надо следить странице.

        Raises:
            CurrentBatchNotCompletedError: Если текущая партия ещё не закрыта.
            LlmRateLimitExceededError: Если лимит генерации исчерпан.
        """
        is_allowed = await self._rate_limiter.is_allowed(
            scope="llm-generation",
            key=str(user_id),
            limit=settings.llm.llm_request_limit,
            window_seconds=settings.llm.llm_request_window_seconds,
        )
        if not is_allowed:
            raise LlmRateLimitExceededError("Лимит генерации временно исчерпан")

        timeout_seconds = settings.app.learning_batch_generation_timeout_seconds
        async with self._uow as uow:
            session_repository = uow.sessions
            progress_repository = uow.progress
            stored = await session_repository.get_track_session(user_id, track)
            session = stored or LearningSession.create(UserID(user_id), track)
            resumed = False

            if session.is_generating and not session.is_generation_stale(timeout_seconds):
                return session.last_generated_batch

            if session.is_generating:
                session.fail_generation()

            if session.needs_retry:
                batch_number = session.retry_generation()
                resumed = True
            else:
                if session.last_generated_batch > 0:
                    is_completed = await progress_repository.is_batch_completed(
                        user_id,
                        track,
                        session.last_generated_batch,
                    )
                    if not is_completed:
                        raise CurrentBatchNotCompletedError(
                            "Сначала закрой текущую партию карточек"
                        )
                batch_number = session.reserve_next_batch()

            await session_repository.save_track_session(session)

        log_event(
            logger,
            logging.INFO,
            "learning.batch_generation_reserved",
            "Reserved a card batch for background generation",
            user_id=user_id,
            track=track.value,
            batch_number=batch_number,
            resumed=resumed,
        )
        return batch_number
