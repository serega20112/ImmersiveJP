from __future__ import annotations

import logging

from src.backend.dependencies.settings import Settings
from src.backend.dto.learning_dto import SpeechPracticePageDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.infrastructure.security import RateLimiter
from src.backend.use_case.learning.get_speech_practice_page import (
    GetSpeechPracticePageUseCase,
)

logger = get_logger(__name__)


class InvalidSpeechWordsError(Exception):
    pass


class SpeechRateLimitExceededError(Exception):
    pass


class GenerateSpeechPracticeUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        get_speech_practice_page_use_case: GetSpeechPracticePageUseCase,
        llm_client: HuggingFaceLLMClient,
        rate_limiter: RateLimiter,
    ):
        self._user_repository = user_repository
        self._get_speech_practice_page_use_case = get_speech_practice_page_use_case
        self._llm_client = llm_client
        self._rate_limiter = rate_limiter

    async def execute(self, user_id: int, words_text: str) -> SpeechPracticePageDTO:
        if len(words_text.strip()) > Settings.text_input_limit:
            raise InvalidSpeechWordsError(
                f"Поле со словами ограничено {Settings.text_input_limit} символами"
            )
        is_allowed = await self._rate_limiter.is_allowed(
            scope="llm-generation",
            key=f"speech:{user_id}",
            limit=Settings.llm_request_limit,
            window_seconds=Settings.llm_request_window_seconds,
        )
        if not is_allowed:
            raise SpeechRateLimitExceededError("Лимит генерации временно исчерпан")

        user = await self._user_repository.get_by_id(user_id)
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
