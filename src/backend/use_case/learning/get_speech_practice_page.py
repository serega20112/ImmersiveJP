from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.dto.learning_dto import SpeechPracticePageDTO
from src.backend.infrastructure.repositories import (
    AbstractContentRepository,
    AbstractSessionRepository,
    AbstractUserRepository,
)


class GetSpeechPracticePageUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        content_repository: AbstractContentRepository,
        session_repository: AbstractSessionRepository,
    ):
        self._user_repository = user_repository
        self._content_repository = content_repository
        self._session_repository = session_repository

    async def execute(self, user_id: int) -> SpeechPracticePageDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        suggested_words, latest_topics = await self._build_language_context(user_id)
        return SpeechPracticePageDTO(
            title="Речевая практика",
            subtitle="По списку слов сервис собирает предложения и короткие диалоги для проговаривания.",
            words_text=", ".join(suggested_words[:8]),
            suggested_words=suggested_words,
            latest_topics=latest_topics,
            skill_summary=(
                user.skill_assessment.summary if user.skill_assessment is not None else None
            ),
        )

    async def _build_language_context(self, user_id: int) -> tuple[list[str], list[str]]:
        session = await self._session_repository.get_track_session(
            user_id,
            TrackType.LANGUAGE,
        )
        cards = []
        if session is not None and session.last_generated_batch > 0:
            cards = await self._content_repository.list_cards_by_batch(
                user_id,
                TrackType.LANGUAGE,
                session.last_generated_batch,
            )
        if not cards:
            completed = await self._content_repository.list_completed_cards(
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
                normalized = term.casefold()
                if normalized in seen_words:
                    continue
                seen_words.add(normalized)
                suggested_words.append(term)
                if len(suggested_words) == 12:
                    return suggested_words, latest_topics[:5]
        return suggested_words, latest_topics[:5]
