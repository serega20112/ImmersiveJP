from __future__ import annotations

from src.application.dto.learning import SpeechPracticePageDTO
from src.application.interfaces import UnitOfWork
from src.application.use_cases.key_terms import key_term_input_value
from src.domain.value_objects.track_type import TrackType


class GetSpeechPracticePageUseCase:
    def __init__(self, uow: UnitOfWork):
        """Initialize the get speech practice page use case.

        Args:
            uow: Unit of work for database transactions.
        """
        self._uow = uow

    async def execute(self, user_id: int) -> SpeechPracticePageDTO:
        """Get the speech practice page for a user.

        Args:
            user_id: ID of the user.

        Returns:
            The speech practice page data.

        Raises:
            ValueError: If the user is not found.
        """
        async with self._uow as uow:
            user_repository = uow.users
            content_repository = uow.learning_cards
            session_repository = uow.sessions
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")
            suggested_words, latest_topics = await self._build_language_context(
                content_repository,
                session_repository,
                user_id,
            )
            return SpeechPracticePageDTO(
                title="Речевая практика",
                subtitle="По списку слов сервис собирает предложения и короткие диалоги для проговаривания.",
                words_text=", ".join(suggested_words[:8]),
                suggested_words=suggested_words,
                latest_topics=latest_topics,
                skill_summary=(
                    user.skill_assessment.summary
                    if user.skill_assessment is not None
                    else None
                ),
            )

    async def _build_language_context(
        self,
        content_repository,
        session_repository,
        user_id: int,
    ) -> tuple[list[str], list[str]]:
        """Build suggested words and latest topics from the user's cards.

        Args:
            content_repository: Repository for content data.
            session_repository: Repository for session data.
            user_id: ID of the user.

        Returns:
            A tuple of (suggested_words, latest_topics).
        """
        session = await session_repository.get_track_session(
            user_id,
            TrackType.LANGUAGE,
        )
        cards = []
        if session is not None and session.last_generated_batch > 0:
            cards = await content_repository.list_cards_by_batch(
                user_id,
                TrackType.LANGUAGE,
                session.last_generated_batch,
            )
        if not cards:
            completed = await content_repository.list_completed_cards(
                user_id,
                TrackType.LANGUAGE,
            )
            cards = completed[-10:]
        suggested_words: list[str] = []
        latest_topics: list[str] = []
        seen_words: set[str] = set()
        for card in cards:
            latest_topics.append(card.topic)
            for term in card.key_terms:
                prepared_term = key_term_input_value(term)
                normalized = prepared_term.casefold()
                if normalized in seen_words:
                    continue
                seen_words.add(normalized)
                suggested_words.append(prepared_term)
                if len(suggested_words) == 12:
                    return suggested_words, latest_topics[:5]
        return suggested_words, latest_topics[:5]
