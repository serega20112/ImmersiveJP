from __future__ import annotations

import logging
from collections.abc import Mapping

import httpx

from src.backend.dependencies.settings import Settings
from src.backend.domain.content import TrackType
from src.backend.domain.mentor import MentorFocus, MentorMessage
from src.backend.domain.user import User
from src.backend.dto.learning import GeneratedCardDraftDTO, SpeechPracticeDTO
from src.backend.dto.mentor_dto import MentorReplyDTO
from src.backend.dto.profile_dto import (
    AIAdviceDTO,
    LearningPlanPageDTO,
    ProgressReportDTO,
)
from src.backend.infrastructure.cache import KeyValueStore
from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.external.llm import fallbacks as fallback_module
from src.backend.infrastructure.external.llm import (
    normalization as normalization_module,
)
from src.backend.infrastructure.external.llm import prompts as prompt_module
from src.backend.infrastructure.external.llm import requests as request_module
from src.backend.infrastructure.external.llm.fallbacks import LLMFallbackMixin
from src.backend.infrastructure.external.llm.normalization import LLMNormalizationMixin
from src.backend.infrastructure.external.llm.prompts import LLMPromptMixin
from src.backend.infrastructure.external.llm.requests import LLMRequestMixin

logger = get_logger(__name__)


class HuggingFaceLLMClient(
    LLMRequestMixin, LLMPromptMixin, LLMNormalizationMixin, LLMFallbackMixin
):
    _CARDS_CACHE_VERSION = "cards-v3"
    _SPEECH_CACHE_VERSION = "speech-v3"
    _ADVICE_CACHE_VERSION = "advice-v3"

    def __init__(self, store: KeyValueStore):
        self._store = store
        self._http_client = httpx.AsyncClient(timeout=Settings.hf_timeout_seconds)

    async def generate_cards(
        self,
        user: User,
        track: TrackType,
        batch_number: int,
        batch_size: int,
        previous_topics: list[str],
        mentor_focus: str | None = None,
    ) -> list[GeneratedCardDraftDTO]:
        payload = {
            "kind": "cards",
            "version": self._CARDS_CACHE_VERSION,
            "user_id": user.id,
            "track": track.value,
            "batch_number": batch_number,
            "batch_size": batch_size,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
            "interests": user.interests,
            "previous_topics": previous_topics,
            "diagnostic_level": (
                user.skill_assessment.estimated_level.value
                if user.skill_assessment and user.skill_assessment.estimated_level
                else None
            ),
            "diagnostic_summary": (
                user.skill_assessment.summary if user.skill_assessment else None
            ),
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
            "mentor_focus": mentor_focus,
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return [GeneratedCardDraftDTO.model_validate(item) for item in cached]

        self._log_cache_miss(payload)
        generated = await self._request_cards(payload)
        await self._store.set_json(
            cache_key,
            [item.model_dump() for item in generated],
            expire_seconds=24 * 60 * 60,
        )
        return generated

    async def generate_advice(
        self, user: User, report: ProgressReportDTO
    ) -> AIAdviceDTO:
        payload = {
            "kind": "advice",
            "version": self._ADVICE_CACHE_VERSION,
            "user_id": user.id,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
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
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return AIAdviceDTO.model_validate(cached)

        self._log_cache_miss(payload)
        advice = await self._request_advice(user, report)
        await self._store.set_json(
            cache_key, advice.model_dump(), expire_seconds=6 * 60 * 60
        )
        return advice

    async def generate_speech_practice(
        self,
        user: User,
        words: list[str],
    ) -> SpeechPracticeDTO:
        payload = {
            "kind": "speech",
            "version": self._SPEECH_CACHE_VERSION,
            "user_id": user.id,
            "goal": user.learning_goal.value if user.learning_goal else None,
            "language_level": (
                user.language_level.value if user.language_level else None
            ),
            "study_timeline": (
                user.study_timeline.value if user.study_timeline else None
            ),
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
            "strengths": (
                list(user.skill_assessment.strengths) if user.skill_assessment else []
            ),
            "weak_points": (
                list(user.skill_assessment.weak_points) if user.skill_assessment else []
            ),
        }
        cache_key = self._cache_key(payload)
        cached = await self._store.get_json(cache_key)
        if cached is not None:
            self._log_cache_hit(payload)
            return SpeechPracticeDTO.model_validate(cached)

        self._log_cache_miss(payload)
        practice = await self._request_speech_practice(payload)
        await self._store.set_json(
            cache_key, practice.model_dump(), expire_seconds=12 * 60 * 60
        )
        return practice

    async def generate_mentor_reply(
        self,
        *,
        user: User,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
        history: list[MentorMessage],
        active_focus: MentorFocus | None,
    ) -> MentorReplyDTO:
        payload = {
            "kind": "mentor",
            "user_id": user.id,
        }
        if not Settings.hf_api_token:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_mentor_reply(report, plan, message, active_focus)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.5,
                system_content=(
                    "Ты наставник ImmersJP. Отвечай только JSON-объектом с полями reply, action_steps, suggested_prompts. "
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
                ),
            )
            log_event(
                logger,
                logging.WARNING,
                "llm.mentor_raw_response",
                "Raw LLM response for mentor",
                parsed_type=type(parsed).__name__,
                parsed_keys=list(parsed.keys()) if isinstance(parsed, Mapping) else [],
                raw_preview=str(parsed)[:600] if parsed else None,
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

    async def close(self) -> None:
        await self._http_client.aclose()


request_module.HuggingFaceLLMClient = HuggingFaceLLMClient
prompt_module.HuggingFaceLLMClient = HuggingFaceLLMClient
normalization_module.HuggingFaceLLMClient = HuggingFaceLLMClient
fallback_module.HuggingFaceLLMClient = HuggingFaceLLMClient
