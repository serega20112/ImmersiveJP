from __future__ import annotations

import logging

from src.application.dto.learning import TrackCardDTO
from src.application.exceptions import LlmRateLimitExceededError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient, RateLimiter
from src.application.interfaces.database import MentorRepositoryPort
from src.application.use_cases.mappers import to_track_card_dto
from src.config.settings import settings
from src.domain.entities.content import LearningCard
from src.domain.entities.progress import CARD_BATCH_SIZE
from src.domain.value_objects.track_type import TrackType
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class GenerateCardsUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        mentor_repository: MentorRepositoryPort,
        llm_client: LLMClient,
        rate_limiter: RateLimiter,
    ):
        """Initialize the generate cards use case.

        Args:
            uow: Unit of work for database transactions.
            mentor_repository: Repository for mentor data.
            llm_client: Client for LLM card generation.
            rate_limiter: Rate limiter for LLM requests.
        """
        self._uow = uow
        self._mentor_repository = mentor_repository
        self._llm_client = llm_client
        self._rate_limiter = rate_limiter

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_size: int = CARD_BATCH_SIZE,
    ) -> list[TrackCardDTO]:
        """Generate a new batch of learning cards for a user.

        Args:
            user_id: ID of the user.
            track: The learning track type.
            batch_size: Number of cards to generate.

        Returns:
            A list of generated track card DTOs.

        Raises:
            LlmRateLimitExceededError: If the LLM rate limit is exceeded.
            ValueError: If the user is not found.
        """
        is_allowed = await self._rate_limiter.is_allowed(
            scope="llm-generation",
            key=str(user_id),
            limit=settings.llm.llm_request_limit,
            window_seconds=settings.llm.llm_request_window_seconds,
        )
        if not is_allowed:
            raise LlmRateLimitExceededError("Лимит генерации временно исчерпан")

        async with self._uow as uow:
            user_repository = uow.repository("user")
            content_repository = uow.repository("content")
            session_repository = uow.repository("session")
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

            session = await session_repository.get_track_session(user_id, track)
            next_batch = session.last_generated_batch + 1 if session else 1
            previous_topics = await content_repository.list_recent_topics(user_id, track)
            active_focus = await self._mentor_repository.get_focus(user_id)
            drafts = await self._llm_client.generate_cards(
                user=user,
                track=track,
                batch_number=next_batch,
                batch_size=batch_size,
                previous_topics=previous_topics,
                mentor_focus=(
                    active_focus.note
                    if active_focus is not None and active_focus.track == track.value
                    else None
                ),
            )
            cards = [
                LearningCard.create(
                    user_id=user_id,
                    track=track,
                    topic=draft.topic,
                    explanation=draft.explanation,
                    examples=draft.examples,
                    key_terms=draft.key_terms,
                    batch_number=next_batch,
                    position=index,
                )
                for index, draft in enumerate(drafts, start=1)
            ]
            saved_cards = await content_repository.add_many(cards)
            await session_repository.upsert_track_session(user_id, track, next_batch)
        log_event(
            logger,
            logging.INFO,
            "learning.cards_generated",
            "Generated learning cards batch",
            user_id=user_id,
            track=track.value,
            batch_number=next_batch,
            cards_count=len(saved_cards),
        )
        return [to_track_card_dto(card, set()) for card in saved_cards]
