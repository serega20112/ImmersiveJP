from __future__ import annotations

import logging

from src.application.dto.learning import SpeechPracticePageDTO
from src.application.exceptions import InvalidSpeechWordsError, SpeechRateLimitExceededError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient, RateLimiter
from src.application.use_cases.learning.speech.get_speech_practice_page import (
    GetSpeechPracticePageUseCase,
)
from src.config.settings import settings
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class GenerateSpeechPracticeUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        get_speech_practice_page_use_case: GetSpeechPracticePageUseCase,
        llm_client: LLMClient,
        rate_limiter: RateLimiter,
    ):
        """Initialize the generate speech practice use case.

        Args:
            uow: Unit of work for database transactions.
            get_speech_practice_page_use_case: Use case for getting speech practice page.
            llm_client: Client for LLM chat completions.
            rate_limiter: Rate limiter for LLM requests.
        """
        self._uow = uow
        self._get_speech_practice_page_use_case = get_speech_practice_page_use_case
        self._llm_client = llm_client
        self._rate_limiter = rate_limiter

    async def execute(self, user_id: int, words_text: str) -> SpeechPracticePageDTO:
        """Generate speech practice content for given words.

        Args:
            user_id: ID of the user.
            words_text: Comma or newline separated words.

        Returns:
            The generated speech practice page data.

        Raises:
            InvalidSpeechWordsError: If words input is invalid.
            SpeechRateLimitExceededError: If the rate limit is exceeded.
        """
        if len(words_text.strip()) > settings.app.text_input_limit:
            raise InvalidSpeechWordsError(
                f"Поле со словами ограничено {settings.app.text_input_limit} символами"
            )
        is_allowed = await self._rate_limiter.is_allowed(
            scope="llm-generation",
            key=f"speech:{user_id}",
            limit=settings.llm.llm_request_limit,
            window_seconds=settings.llm.llm_request_window_seconds,
        )
        if not is_allowed:
            raise SpeechRateLimitExceededError("Лимит генерации временно исчерпан")

        async with self._uow as uow:
            user_repository = uow.users
            user = await user_repository.get_by_id(user_id)
            if user is None:
                raise ValueError("Пользователь не найден")

        page = await self._get_speech_practice_page_use_case.execute(user_id)
        words = self._parse_words(words_text)
        if not words:
            words = list(page.suggested_words)
        if len(words) < 3:
            raise InvalidSpeechWordsError(
                "Нужно хотя бы 3 слова или термина, иначе речи не из чего собираться"
            )

        practice = await self._llm_client.generate_speech_practice(user, words[:40])
        log_event(
            logger,
            logging.INFO,
            "learning.speech_generated",
            "Generated speech practice",
            user_id=user_id,
            words_count=len(words[:40]),
        )
        return page.model_copy(
            update={
                "words_text": ", ".join(words[:40]),
                "practice": practice,
            }
        )

    @staticmethod
    def _parse_words(raw_value: str) -> list[str]:
        """Parse a raw words string into a deduplicated list.

        Args:
            raw_value: Comma or newline separated words.

        Returns:
            A list of unique word strings.
        """
        prepared = raw_value.replace("\r", "\n").replace(";", ",")
        result: list[str] = []
        seen: set[str] = set()
        for chunk in prepared.split("\n"):
            for part in chunk.split(","):
                value = part.strip()
                normalized = value.casefold()
                if not value or normalized in seen:
                    continue
                seen.add(normalized)
                result.append(value)
        return result
