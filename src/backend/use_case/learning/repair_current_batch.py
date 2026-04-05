from __future__ import annotations

from src.backend.domain.content import LearningCard, TrackType
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractSessionRepository,
    AbstractUserRepository,
)


class RepairCurrentBatchUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        content_repository: AbstractContentRepository,
        session_repository: AbstractSessionRepository,
        llm_client: HuggingFaceLLMClient,
    ):
        self._user_repository = user_repository
        self._content_repository = content_repository
        self._session_repository = session_repository
        self._llm_client = llm_client

    async def execute(self, user_id: int, track: TrackType) -> None:
        session = await self._session_repository.get_track_session(user_id, track)
        if session is None or session.last_generated_batch <= 0:
            return

        current_batch = session.last_generated_batch
        batch_cards = await self._content_repository.list_cards_by_batch(
            user_id,
            track,
            current_batch,
        )
        broken_cards = [card for card in batch_cards if self._is_placeholder(card.topic)]
        if not broken_cards:
            return

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            return

        previous_topics = await self._content_repository.list_recent_topics(
            user_id,
            track,
            limit=40,
        )
        clean_previous_topics = [
            topic
            for topic in previous_topics
            if not self._is_placeholder(topic)
        ]
        drafts = await self._llm_client.generate_cards(
            user=user,
            track=track,
            batch_number=current_batch,
            batch_size=len(broken_cards),
            previous_topics=clean_previous_topics,
        )
        replacements = [
            LearningCard(
                id=int(card.id or 0),
                user_id=card.user_id,
                track=card.track,
                topic=draft.topic,
                explanation=draft.explanation,
                examples=draft.examples,
                key_terms=draft.key_terms,
                batch_number=card.batch_number,
                position=card.position,
                created_at=card.created_at,
            )
            for card, draft in zip(broken_cards, drafts, strict=False)
        ]
        await self._content_repository.update_many(replacements)

    @staticmethod
    def _is_placeholder(topic: str) -> bool:
        return topic.strip().casefold().startswith("резервная тема")
