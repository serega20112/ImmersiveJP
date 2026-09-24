from __future__ import annotations

import logging

from src.application.dto.learning import GeneratedCardBatchDTO, GeneratedCardDraftDTO
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient
from src.application.interfaces.database import MentorRepositoryPort
from src.domain.aggregates.user import User
from src.domain.entities.content import LearningCard
from src.domain.entities.progress import CARD_BATCH_SIZE
from src.domain.value_objects import TrackType, UserID
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class GenerateCardsUseCase:
    """Дописать партию карточек, забронированную заранее.

    Транзакция на каждую карточку, а не одна на партию: смысл брони в том,
    чтобы страница показывала готовые карточки, пока остальные ещё пишутся.
    Один большой транзакционный блок показал бы всё разом через четверть минуты
    либо не показал бы ничего при обрыве.

    Атрибуты:
        _uow: Единица работы с базой.
        _mentor_repository: Репозиторий фокуса наставника.
        _llm_client: Клиент генерации.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        mentor_repository: MentorRepositoryPort,
        llm_client: LLMClient,
    ):
        """Инициализировать юзкейс генерации карточек.

        Args:
            uow: Единица работы с базой.
            mentor_repository: Репозиторий фокуса наставника.
            llm_client: Клиент генерации.
        """
        self._uow = uow
        self._mentor_repository = mentor_repository
        self._llm_client = llm_client

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        batch_size: int = CARD_BATCH_SIZE,
    ) -> GeneratedCardBatchDTO:
        """Сгенерировать и по одной записать недостающие карточки партии.

        Обращение к модели выполняется вне транзакции: ранее та держалась все
        десятки секунд ответа, удерживая соединение пула и блокируя отчёт о
        прогрессе партии.

        Неудача не выбрасывается наружу: вызов идёт из отсоединённой фоновой
        задачи, где исключение никто не поймает, кроме лога. Единственный
        канал связи со страницей — состояние партии в базе, плюс громкая запись
        в журнале.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            batch_number: Номер забронированной партии.
            batch_size: Размер партии.

        Returns:
            Партию черновиков с разделением по источнику.
        """
        existing_count = await self._persisted_count(user_id, track, batch_number)
        remaining = batch_size - existing_count
        if remaining <= 0:
            await self._settle(user_id, track, succeeded=True)
            return GeneratedCardBatchDTO(drafts=[], model_count=0, fallback_count=0)

        try:
            user, previous_topics, mentor_focus = await self._load_context(user_id, track)
            batch = await self._llm_client.generate_cards(
                user=user,
                track=track,
                batch_number=batch_number,
                batch_size=remaining,
                previous_topics=previous_topics,
                mentor_focus=mentor_focus,
            )
            await self._append_cards(
                user_id,
                track,
                batch_number,
                start_position=existing_count + 1,
                drafts=batch.drafts,
            )
        except Exception as error:
            await self._settle(user_id, track, succeeded=False)
            log_event(
                logger,
                logging.ERROR,
                "learning.batch_generation_finished",
                "Card batch generation stopped before the batch was complete",
                user_id=user_id,
                track=track.value,
                batch_number=batch_number,
                state="failed",
                error=str(error),
            )
            return GeneratedCardBatchDTO(drafts=[], model_count=0, fallback_count=0)

        await self._settle(user_id, track, succeeded=True)
        log_event(
            logger,
            logging.INFO,
            "learning.batch_generation_finished",
            "Card batch generation finished",
            user_id=user_id,
            track=track.value,
            batch_number=batch_number,
            state="ready",
            model_count=batch.model_count,
            fallback_count=batch.fallback_count,
            written=len(batch.drafts),
        )
        return batch

    async def _persisted_count(self, user_id: int, track: TrackType, batch_number: int) -> int:
        """Посчитать, сколько карточек партии уже лежит в базе.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            batch_number: Номер партии.

        Returns:
            Количество уже записанных карточек.
        """
        async with self._uow as uow:
            content_repository = uow.repository("content")
            cards = await content_repository.list_cards_by_batch(user_id, track, batch_number)
        return len(cards)

    async def _load_context(
        self,
        user_id: int,
        track: TrackType,
    ) -> tuple[User, list[str], str | None]:
        """Прочитать пользователя, прошлые темы и фокус наставника.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.

        Returns:
            Кортеж из пользователя, списка тем и записки наставника.

        Raises:
            LookupError: Если пользователь не найден.
        """
        async with self._uow as uow:
            user_repository = uow.repository("user")
            content_repository = uow.repository("content")
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise LookupError("Пользователь не найден")
            previous_topics = await content_repository.list_recent_topics(user_id, track)
        active_focus = await self._mentor_repository.get_focus(user_id)
        mentor_focus = (
            active_focus.note
            if active_focus is not None and active_focus.track == track.value
            else None
        )
        return user, previous_topics, mentor_focus

    async def _append_cards(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
        start_position: int,
        drafts: list[GeneratedCardDraftDTO],
    ) -> None:
        """Записать карточки, фиксируя каждую отдельной транзакцией.

        Каждая карточка живёт в своём входе в единицу работы: выход из неё
        коммитит, и уже через мгновение карточку видит опрос страницы. Одна
        транзакция на партию вернула бы ровно то, от чего уходили,
        — молчаливое ожидание всего батча.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            batch_number: Номер партии.
            start_position: Позиция первой записываемой карточки.
            drafts: Черновики карточек в порядке партии.
        """
        for offset, draft in enumerate(drafts):
            card = LearningCard.create(
                user_id=UserID(user_id),
                track=track,
                topic=draft.topic,
                explanation=draft.explanation,
                examples=list(draft.examples),
                key_terms=list(draft.key_terms),
                batch_number=batch_number,
                position=start_position + offset,
            )
            async with self._uow as uow:
                content_repository = uow.repository("content")
                await content_repository.create(card)

    async def _settle(self, user_id: int, track: TrackType, *, succeeded: bool) -> None:
        """Перевести сессию из генерации в готовность либо в оборванный статус.

        Args:
            user_id: Идентификатор пользователя.
            track: Тип трека.
            succeeded: Завершилась ли генерация.
        """
        async with self._uow as uow:
            session_repository = uow.repository("session")
            session = await session_repository.get_track_session(user_id, track)
            if session is None or not session.is_generating:
                return
            if succeeded:
                session.finish_generation()
            else:
                session.fail_generation()
            await session_repository.save_track_session(session)
