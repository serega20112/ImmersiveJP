from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from src.application.dto.learning import (
    GeneratedCardBatchDTO,
    GeneratedCardDraftDTO,
    SpeechPracticeDTO,
    TrackWorkResultDTO,
)
from src.application.dto.mentor import MentorReplyDTO
from src.application.dto.profile import (
    AIAdviceDTO,
    LearningPlanPageDTO,
    ProgressReportDTO,
)
from src.config.settings import settings
from src.domain.aggregates.user import User
from src.domain.entities.mentor import MentorFocus, MentorMessage
from src.domain.value_objects.track_type import TrackType
from src.infrastructures.cache import KeyValueStore
from src.infrastructures.external.llm import fallbacks as fallback_module
from src.infrastructures.external.llm import (
    normalization as normalization_module,
)
from src.infrastructures.external.llm import prompts as prompt_module
from src.infrastructures.external.llm import requests as request_module
from src.infrastructures.external.llm.fallback_content import ensure_available
from src.infrastructures.external.llm.fallbacks import LLMFallbackMixin
from src.infrastructures.external.llm.normalization import LLMNormalizationMixin
from src.infrastructures.external.llm.prompts import LLMPromptMixin
from src.infrastructures.external.llm.requests import LLMRequestMixin
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)


class HuggingFaceLLMClient(
    LLMRequestMixin, LLMPromptMixin, LLMNormalizationMixin, LLMFallbackMixin
):
    _CARDS_CACHE_VERSION = "cards-v5"
    _SPEECH_CACHE_VERSION = "speech-v3"
    _ADVICE_CACHE_VERSION = "advice-v3"
    _CARDS_TTL_SECONDS = 24 * 60 * 60
    _SPEECH_TTL_SECONDS = 12 * 60 * 60
    _ADVICE_TTL_SECONDS = 6 * 60 * 60

    def __init__(self, store: KeyValueStore) -> None:
        """Инициализировать клиента генерации.

        Args:
            store: Key-value хранилище кэша ответов и состояния предохранителя.
        """
        self._store = store
        self._http_client = httpx.AsyncClient(timeout=settings.llm.hf_timeout_seconds)
        self._generation_locks: dict[str, asyncio.Lock] = {}
        ensure_available()
        self._warn_incomplete_fallback()

    @staticmethod
    def _warn_incomplete_fallback() -> None:
        """Сообщить о настроенном наполовину резервном провайдере.

        OpenRouter включается только когда есть и ключ, и модель. Частая ошибка —
        положить ключ и оставить OPENROUTER_MODEL пустым: резерв молча не участвует,
        и при исчерпанном основном токене генерация уходит в заготовки, ничем не
        выдавая неправильную настройку.
        """
        has_key = bool(settings.llm.openrouter_api_tokens)
        has_model = bool(settings.llm.openrouter_model.strip())
        if has_key == has_model:
            return
        missing = "OPENROUTER_MODEL" if has_key else "OPENROUTER_API_KEY"
        log_event(
            logger,
            logging.WARNING,
            "llm.fallback_incomplete",
            "OpenRouter fallback is configured only partially and will not be used",
            missing_variable=missing,
        )

    @asynccontextmanager
    async def _single_flight(self, cache_key: str) -> AsyncIterator[None]:
        """Не дать параллельным одинаковым генерациям пройти в модель дважды.

        Защита действует в рамках одного процесса. Для нескольких воркеров
        нужна блокировка в хранилище; здесь сознательно выбран более простой
        вариант, потому что он снимает основной случай — две загрузки одной
        страницы одним процессом.

        Args:
            cache_key: Ключ генерации, по которому группируются вызовы.

        Yields:
            Контекст, внутри которого стоит проверять кэш и писать результат.
        """
        lock = self._generation_locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            try:
                yield
            finally:
                if not lock.locked():
                    self._generation_locks.pop(cache_key, None)

    async def generate_cards(
        self,
        user: User,
        track: TrackType,
        batch_number: int,
        batch_size: int,
        previous_topics: list[str],
        previous_key_terms: list[str] | None = None,
        mentor_focus: str | None = None,
    ) -> GeneratedCardBatchDTO:
        payload = {
            "kind": "cards",
            "version": self._CARDS_CACHE_VERSION,
            "user_id": int(user.id) if user.id is not None else None,
            "track": track.value,
            "batch_number": batch_number,
            "batch_size": batch_size,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (user.language_level.value if user.language_level else None),
            "study_timeline": (user.study_timeline.value if user.study_timeline else None),
            "interests": user.interests,
            "previous_topics": previous_topics,
            "previous_key_terms": previous_key_terms or [],
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (list(user.skill_assessment.strengths) if user.skill_assessment else []),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
            "mentor_focus": mentor_focus,
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return self._cached_card_batch(cached)

        async with self._single_flight(cache_key):
            cached = await self._store.get_json(cache_key)
            if cached is not None:
                self._log_cache_hit(payload)
                return self._cached_card_batch(cached)
            self._log_cache_miss(payload)
            result = await self._request_cards(payload)
            if result.generated:
                await self._store.set_json(
                    cache_key,
                    [item.model_dump() for item in result.value.drafts],
                    expire_seconds=self._CARDS_TTL_SECONDS,
                )
            return result.value

    @staticmethod
    def _cached_card_batch(cached: list) -> GeneratedCardBatchDTO:
        """Собрать партию из кэша.

        В кэш попадает только целиком модельная партия, поэтому здесь нечего
        считать: все карточки числятся пришедшими от модели.

        Args:
            cached: Сохранённые черновики карточек.

        Returns:
            Партию черновиков с модельным источником.
        """
        drafts = [GeneratedCardDraftDTO.model_validate(item) for item in cached]
        return GeneratedCardBatchDTO(drafts=drafts, model_count=len(drafts), fallback_count=0)

    async def generate_advice(self, user: User, report: ProgressReportDTO) -> AIAdviceDTO:
        payload = {
            "kind": "advice",
            "version": self._ADVICE_CACHE_VERSION,
            "user_id": int(user.id) if user.id is not None else None,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (user.language_level.value if user.language_level else None),
            "study_timeline": (user.study_timeline.value if user.study_timeline else None),
            "interests": user.interests,
            "report": report.model_dump(),
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (list(user.skill_assessment.strengths) if user.skill_assessment else []),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return AIAdviceDTO.model_validate(cached)

        async with self._single_flight(cache_key):
            cached = await self._store.get_json(cache_key)
            if cached is not None:
                self._log_cache_hit(payload)
                return AIAdviceDTO.model_validate(cached)
            self._log_cache_miss(payload)
            result = await self._request_advice(user, report)
            if result.generated:
                await self._store.set_json(
                    cache_key,
                    result.value.model_dump(),
                    expire_seconds=self._ADVICE_TTL_SECONDS,
                )
            return result.value

    async def generate_speech_practice(
        self,
        user: User,
        words: list[str],
    ) -> SpeechPracticeDTO:
        payload = {
            "kind": "speech",
            "version": self._SPEECH_CACHE_VERSION,
            "user_id": int(user.id) if user.id is not None else None,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (user.language_level.value if user.language_level else None),
            "study_timeline": (user.study_timeline.value if user.study_timeline else None),
            "interests": user.interests,
            "words": words,
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (list(user.skill_assessment.strengths) if user.skill_assessment else []),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return SpeechPracticeDTO.model_validate(cached)

        async with self._single_flight(cache_key):
            cached = await self._store.get_json(cache_key)
            if cached is not None:
                self._log_cache_hit(payload)
                return SpeechPracticeDTO.model_validate(cached)
            self._log_cache_miss(payload)
            result = await self._request_speech_practice(payload)
            if result.generated:
                await self._store.set_json(
                    cache_key,
                    result.value.model_dump(),
                    expire_seconds=self._SPEECH_TTL_SECONDS,
                )
            return result.value

    async def generate_mentor_reply(
        self,
        *,
        user: User,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
        history: list[MentorMessage],
        active_focus: MentorFocus | None,
        document_context: str = "",
    ) -> MentorReplyDTO:
        payload = {
            "kind": "mentor",
            "user_id": int(user.id) if user.id is not None else None,
        }
        if not settings.llm.has_llm_credentials:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_mentor_reply(report, plan, message, active_focus)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.5,
                system_content=(
                    "Ты наставник ImmersJP. "
                    'Верни строго один JSON-объект вида {"reply": "...", '
                    '"action_steps": ["...", "...", "..."], "suggested_prompts": ["...", "..."]}. '
                    "reply должен быть одним коротким абзацем до 320 символов. "
                    "action_steps: ровно 3 коротких шага до 80 символов каждый. "
                    "suggested_prompts: ровно 2 коротких вопроса до 60 символов каждый. "
                    "Без markdown, без reasoning, без текста вне JSON."
                ),
                user_content=self._build_mentor_prompt(
                    user=user,
                    report=report,
                    plan=plan,
                    message=message,
                    history=history,
                    document_context=document_context,
                ),
            )
            return self._normalize_mentor_reply(parsed, report, plan, active_focus)
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "llm.mentor_request_exception",
                "Exception during mentor LLM request",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            self._log_fallback(
                payload,
                reason=self._fallback_reason_from_error(error),
            )
            return self._fallback_mentor_reply(report, plan, message, active_focus)

    async def generate_knowledge_check(
        self,
        *,
        user: User,
        weak_points: list[str] | None = None,
        strengths: list[str] | None = None,
        recent_topics: list[str] | None = None,
        focus_area: str = "",
    ) -> list[dict]:
        payload = {
            "kind": "knowledge_check",
            "user_id": int(user.id) if user.id is not None else None,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (user.language_level.value if user.language_level else None),
            "study_timeline": (user.study_timeline.value if user.study_timeline else None),
            "weak_points": weak_points or [],
            "strengths": strengths or [],
            "recent_topics": recent_topics or [],
            "focus_area": focus_area or "общая проверка",
        }
        if not settings.llm.has_llm_credentials:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_knowledge_check(payload)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.5,
                system_content=(
                    "Ты преподаватель японского. Верни JSON-массив объектов. "
                    "Без markdown, без текста вне JSON."
                ),
                user_content=self._build_knowledge_check_prompt(payload),
            )
            raw_items = parsed if isinstance(parsed, list) else []
            return self._normalize_knowledge_check(raw_items)
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "llm.knowledge_check_exception",
                "Exception during knowledge check generation",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            self._log_fallback(payload, reason=self._fallback_reason_from_error(error))
            return self._fallback_knowledge_check(payload)

    async def evaluate_knowledge_check(
        self,
        *,
        user_id: int = 0,
        questions: list[dict],
        answers: dict[str, str],
    ) -> dict:
        payload = {
            "kind": "knowledge_eval",
            "user_id": user_id,
        }
        eval_payload = {
            "questions": questions,
            "answers": answers,
        }
        if not settings.llm.has_llm_credentials:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_knowledge_eval(questions, answers)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.2,
                system_content=(
                    "Ты преподаватель японского. Верни JSON-объект с полями results, score, summary. "
                    "Без markdown, без текста вне JSON."
                ),
                user_content=self._build_knowledge_eval_prompt(eval_payload),
            )
            return self._normalize_knowledge_eval(parsed, questions, answers)
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "llm.knowledge_eval_exception",
                "Exception during knowledge check evaluation",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            self._log_fallback(payload, reason=self._fallback_reason_from_error(error))
            return self._fallback_knowledge_eval(questions, answers)

    async def review_track_work(
        self,
        *,
        user: User,
        track: TrackType,
        batch_number: int,
        tasks: list[dict[str, object]],
        fallback_result: TrackWorkResultDTO,
    ) -> TrackWorkResultDTO:
        payload = {
            "kind": "work_review",
            "user_id": int(user.id) if user.id is not None else None,
            "track": track.value,
            "batch_number": batch_number,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (user.language_level.value if user.language_level else None),
            "study_timeline": (user.study_timeline.value if user.study_timeline else None),
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "tasks": tasks,
        }
        return await self._request_work_review(payload, fallback_result)

    async def close(self) -> None:
        await self._http_client.aclose()


request_module.HuggingFaceLLMClient = HuggingFaceLLMClient
prompt_module.HuggingFaceLLMClient = HuggingFaceLLMClient
normalization_module.HuggingFaceLLMClient = HuggingFaceLLMClient
fallback_module.HuggingFaceLLMClient = HuggingFaceLLMClient
