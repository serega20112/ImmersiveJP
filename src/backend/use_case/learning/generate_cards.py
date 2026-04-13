from __future__ import annotations

import logging

from src.backend.dependencies.settings import Settings
from src.backend.domain.content import LearningCard, TrackType
from src.backend.domain.progress import CARD_BATCH_SIZE
from src.backend.dto.learning_dto import TrackCardDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractMentorRepository,
    AbstractSessionRepository,
    AbstractUserRepository,
)
from src.backend.infrastructure.security import RateLimiter
from src.backend.use_case.mappers import to_track_card_dto

logger = get_logger(__name__)


class LlmRateLimitExceededError(Exception):
    pass


class GenerateCardsUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        content_repository: AbstractContentRepository,
        session_repository: AbstractSessionRepository,
        mentor_repository: AbstractMentorRepository,
        llm_client: HuggingFaceLLMClient,
        rate_limiter: RateLimiter,
    ):
        self._user_repository = user_repository
        self._content_repository = content_repository
        self._session_repository = session_repository
        self._mentor_repository = mentor_repository
        self._llm_client = llm_client
        self._rate_limiter = rate_limiter

    async def execute(
        self,
        user_id: int,
        track: TrackType,
        batch_size: int = CARD_BATCH_SIZE,
    ) -> list[TrackCardDTO]:
        is_allowed = await self._rate_limiter.is_allowed(
            scope="llm-generation",
            key=str(user_id),
            limit=Settings.llm_request_limit,
            window_seconds=Settings.llm_request_window_seconds,
        )
        if not is_allowed:
            raise LlmRateLimitExceededError("Лимит генерации временно исчерпан")

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        session = await self._session_repository.get_track_session(user_id, track)
        next_batch = session.last_generated_batch + 1 if session else 1
        previous_topics = await self._content_repository.list_recent_topics(
            user_id, track
        )
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
            LearningCard(
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
        saved_cards = await self._content_repository.add_many(cards)
        await self._session_repository.upsert_track_session(user_id, track, next_batch)
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
