from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Mapping
from hashlib import sha256
from json import JSONDecoder

import httpx

from src.backend.dependencies.settings import Settings
from src.backend.dto.learning import TrackWorkResultDTO
from src.backend.domain.user import User
from src.backend.dto.profile_dto import ProgressReportDTO
from src.backend.infrastructure.observability import get_logger, log_event

logger = get_logger(__name__)


class LLMRequestMixin:
    async def _request_cards(self, payload: dict) -> list[GeneratedCardDraftDTO]:
        if not Settings.hf_api_token:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_cards(payload)
        circuit_reason = await self._get_open_circuit_reason(payload)
        if circuit_reason:
            self._log_circuit_open(payload, circuit_reason=circuit_reason)
            self._log_fallback(payload, reason="circuit_open")
            return self._fallback_cards(payload)
        prompt = self._build_cards_prompt(payload)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.35,
                system_content=(
                    "Ты методист по Японии. Верни только компактный JSON-массив без текста вне JSON. "
                    "Ровно по одной карточке на каждый запрошенный элемент. "
                    "Каждая карточка должна содержать topic, explanation, key_terms. "
                    "examples можно вернуть пустым массивом или дать не больше 2 очень коротких строк. "
                    "explanation делай кратким и прикладным. key_terms: ровно 3 строки."
                ),
                user_content=prompt,
            )
            normalized = self._normalize_cards(parsed, payload)
            await self._close_circuit(payload)
            return normalized
        except Exception as error:
            reason = self._fallback_reason_from_error(error)
            await self._open_circuit(payload, reason=reason, error=error)
            self._log_fallback(
                payload,
                reason=reason,
            )
            return self._fallback_cards(payload)

    async def _request_advice(
        self, user: User, report: ProgressReportDTO
    ) -> AIAdviceDTO:
        if not Settings.hf_api_token:
            self._log_fallback(
                {"kind": "advice", "user_id": user.id}, reason="missing_token"
            )
            return self._fallback_advice(user, report)
        try:
            parsed = await self._request_llm_json(
                payload={"kind": "advice", "user_id": user.id},
                temperature=0.6,
                system_content=(
                    "Ты редактор учебных рекомендаций ImmersJP. "
                    "Верни только JSON-объект с полями headline, summary, focus_points. "
                    "Тон спокойный, короткий, практический."
                ),
                user_content=self._build_advice_prompt(user, report),
            )
            return self._normalize_advice_payload(parsed, user, report)
        except Exception as error:
            self._log_fallback(
                {"kind": "advice", "user_id": user.id},
                reason=self._fallback_reason_from_error(error),
            )
            return self._fallback_advice(user, report)

    async def _request_speech_practice(self, payload: dict) -> SpeechPracticeDTO:
        if not Settings.hf_api_token:
            self._log_fallback(payload, reason="missing_token")
            return self._fallback_speech_practice(payload)
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.7,
                system_content=(
                    "Верни только JSON-объект с полями sentences, dialogues, coaching_tip, difficulty_label. "
                    "sentences: ровно 10 коротких объектов. "
                    "dialogues: ровно 5 коротких объектов, в каждом ровно 2 turns. "
                    "Все строки короткие, без markdown, без reasoning, без текста вне JSON."
                ),
                user_content=self._build_speech_prompt(payload),
            )
            return self._normalize_speech_practice(parsed, payload)
        except Exception as error:
            self._log_fallback(
                payload,
                reason=self._fallback_reason_from_error(error),
            )
            return self._fallback_speech_practice(payload)

    async def _request_work_review(
        self,
        payload: dict,
        fallback_result: TrackWorkResultDTO,
    ) -> TrackWorkResultDTO:
        if not Settings.hf_api_token:
            self._log_fallback(payload, reason="missing_token")
            return fallback_result
        try:
            parsed = await self._request_llm_json(
                payload=payload,
                temperature=0.2,
                system_content=(
                    "Ты проверяешь учебную работу ImmersJP. "
                    "Верни только JSON-объект с полями summary, verdict, task_results, certificate_statement. "
                    "task_results: массив объектов с полями task_id, is_correct, feedback. "
                    "feedback должен быть коротким и конкретным. "
                    "Для recall сверяйся с expected_answers. "
                    "Для production и immersion разрешай перефразировку по смыслу, но не засчитывай ответы не по теме. "
                    "Без markdown, без reasoning, без текста вне JSON."
                ),
                user_content=self._build_work_review_prompt(payload, fallback_result),
            )
            return self._normalize_work_review(parsed, payload, fallback_result)
        except Exception as error:
            self._log_fallback(
                payload,
                reason=self._fallback_reason_from_error(error),
            )
            return fallback_result

    async def _request_llm_json(
        self,
        *,
        payload: dict,
        temperature: float,
        system_content: str,
        user_content: str,
    ):
        last_error: Exception | None = None
        request_model, timeout_seconds, retry_attempts, max_tokens = (
            self._request_runtime(payload)
        )
        request_body = {
            "model": request_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        }
        if max_tokens is not None:
            request_body["max_tokens"] = max_tokens
        reasoning_effort = self._request_reasoning_effort(payload)
        if reasoning_effort is not None:
            request_body["reasoning_effort"] = reasoning_effort

        for attempt in range(1, retry_attempts + 1):
            started_at = time.perf_counter()
            try:
                response = await self._http_client.post(
                    Settings.hf_api_url,
                    headers={
                        "Authorization": f"Bearer {Settings.hf_api_token}",
                        "Content-Type": "application/json",
                    },
                    json=request_body,
                    timeout=timeout_seconds,
                )
                response.raise_for_status()
                response_payload = response.json()
                content = self._extract_response_content(response_payload)
                parsed = self._extract_json(content)
                choice = self._extract_first_choice(response_payload)
                log_event(
                    logger,
                    logging.INFO,
                    "llm.request_succeeded",
                    "LLM request succeeded",
                    attempt=attempt,
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                    status_code=response.status_code,
                    model=request_model,
                    provider=Settings.hf_provider,
                    finish_reason=(
                        str(choice.get("finish_reason") or "")
                        if isinstance(choice, Mapping)
                        else None
                    ),
                    content_length=len(content),
                    parsed_type=type(parsed).__name__,
                    parsed_keys=(
                        list(parsed.keys())[:8] if isinstance(parsed, Mapping) else None
                    ),
                    **self._payload_log_fields(payload),
                )
                return parsed
            except Exception as error:
                last_error = error
                log_event(
                    logger,
                    logging.WARNING,
                    "llm.request_failed",
                    "LLM request failed",
                    attempt=attempt,
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                    error_type=type(error).__name__,
                    error_message=str(error),
                    model=request_model,
                    provider=Settings.hf_provider,
                    fallback_reason=self._fallback_reason_from_error(error),
                    **self._response_error_log_fields(error),
                    **self._payload_log_fields(payload),
                )
                if attempt < retry_attempts and self._should_retry_request(error):
                    await asyncio.sleep(Settings.hf_retry_backoff_seconds * attempt)
                else:
                    break

        if last_error is None:
            raise RuntimeError("LLM request failed without a captured exception")
        raise last_error

    @staticmethod
    def _cache_key(payload: dict) -> str:
        dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return f"llm:{sha256(dumped.encode('utf-8')).hexdigest()}"

    def _log_cache_hit(self, payload: dict) -> None:
        log_event(
            logger,
            logging.INFO,
            "llm.cache_hit",
            "LLM cache hit",
            **self._payload_log_fields(payload),
        )

    def _log_cache_miss(self, payload: dict) -> None:
        log_event(
            logger,
            logging.INFO,
            "llm.cache_miss",
            "LLM cache miss",
            **self._payload_log_fields(payload),
        )

    def _log_fallback(self, payload: dict, *, reason: str) -> None:
        log_event(
            logger,
            logging.WARNING,
            "llm.fallback_used",
            "LLM fallback used",
            reason=reason,
            **self._payload_log_fields(payload),
        )

    async def _get_open_circuit_reason(self, payload: dict) -> str | None:
        if str(payload.get("kind") or "") != "cards":
            return None
        circuit_state = await self._store.get_json(self._circuit_key(payload))
        if not isinstance(circuit_state, Mapping):
            return None
        reason = str(circuit_state.get("reason") or "").strip()
        if self._should_bypass_open_circuit(payload, circuit_state, reason=reason):
            return None
        return reason or "request_failed"

    async def _open_circuit(
        self,
        payload: dict,
        *,
        reason: str,
        error: Exception,
    ) -> None:
        if str(payload.get("kind") or "") != "cards":
            return
        if not self._should_open_circuit(error):
            return
        await self._store.set_json(
            self._circuit_key(payload),
            {
                "reason": reason,
                "track": payload.get("track"),
                "batch_size": payload.get("batch_size"),
            },
            expire_seconds=Settings.hf_cards_circuit_open_seconds,
        )
        log_event(
            logger,
            logging.WARNING,
            "llm.circuit_opened",
            "Opened LLM circuit for cards",
            reason=reason,
            cooldown_seconds=Settings.hf_cards_circuit_open_seconds,
            model=self._request_runtime(payload)[0],
            provider=Settings.hf_provider,
            **self._payload_log_fields(payload),
        )

    async def _close_circuit(self, payload: dict) -> None:
        if str(payload.get("kind") or "") != "cards":
            return
        await self._store.delete(self._circuit_key(payload))

    def _log_circuit_open(self, payload: dict, *, circuit_reason: str) -> None:
        log_event(
            logger,
            logging.WARNING,
            "llm.circuit_open",
            "LLM circuit already open for cards",
            reason=circuit_reason,
            cooldown_seconds=Settings.hf_cards_circuit_open_seconds,
            model=self._request_runtime(payload)[0],
            provider=Settings.hf_provider,
            **self._payload_log_fields(payload),
        )

    @staticmethod
    def _should_bypass_open_circuit(
        payload: Mapping[str, object],
        circuit_state: Mapping[str, object],
        *,
        reason: str,
    ) -> bool:
        if reason != "timeout":
            return False

        current_track = str(payload.get("track") or "").strip()
        stored_track = str(circuit_state.get("track") or "").strip()
        if not stored_track:
            return True
        if current_track and stored_track != current_track:
            return True

        current_batch_size = LLMRequestMixin._coerce_int(payload.get("batch_size"))
        stored_batch_size = LLMRequestMixin._coerce_int(circuit_state.get("batch_size"))
        if stored_batch_size is None:
            return True
        if current_batch_size is None:
            return False
        return current_batch_size < stored_batch_size

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                return int(stripped)
        return None

    @staticmethod
    def _circuit_key(payload: dict) -> str:
        request_model = LLMRequestMixin._request_runtime(payload)[0]
        provider = (Settings.hf_provider or "").strip() or "default"
        kind = str(payload.get("kind") or "unknown")
        return f"llm:circuit:{kind}:{provider}:{request_model}"

    @staticmethod
    def _request_runtime(payload: dict) -> tuple[str, float, int, int | None]:
        kind = str(payload.get("kind") or "")
        if kind == "cards":
            model = Settings.hf_cards_model.strip() or Settings.hf_model.strip()
            timeout_seconds = Settings.hf_cards_timeout_seconds
            retry_attempts = Settings.hf_cards_retry_attempts
            max_tokens = Settings.hf_cards_max_tokens
        elif kind == "mentor":
            model = Settings.hf_mentor_model.strip() or Settings.hf_model.strip()
            timeout_seconds = Settings.hf_mentor_timeout_seconds
            retry_attempts = Settings.hf_mentor_retry_attempts
            max_tokens = Settings.hf_mentor_max_tokens
        elif kind == "speech":
            model = Settings.hf_speech_model.strip() or Settings.hf_model.strip()
            timeout_seconds = Settings.hf_speech_timeout_seconds
            retry_attempts = Settings.hf_speech_retry_attempts
            max_tokens = Settings.hf_speech_max_tokens
        elif kind == "work_review":
            model = (
                Settings.hf_work_review_model.strip()
                or Settings.hf_mentor_model.strip()
                or Settings.hf_model.strip()
            )
            timeout_seconds = Settings.hf_work_review_timeout_seconds
            retry_attempts = Settings.hf_work_review_retry_attempts
            max_tokens = Settings.hf_work_review_max_tokens
        else:
            model = Settings.hf_model.strip()
            timeout_seconds = Settings.hf_timeout_seconds
            retry_attempts = Settings.hf_retry_attempts
            max_tokens = None
        return (
            HuggingFaceLLMClient._resolve_request_model(model),
            timeout_seconds,
            max(retry_attempts, 1),
            max_tokens,
        )

    @staticmethod
    def _request_reasoning_effort(payload: dict) -> str | None:
        kind = str(payload.get("kind") or "")
        if kind in {"cards", "mentor", "speech", "work_review"}:
            return "low"
        return None

    @staticmethod
    def _resolve_request_model(model: str) -> str:
        provider = (Settings.hf_provider or "").strip()
        if not model:
            return model
        if ":" in model or not provider:
            return model
        if HuggingFaceLLMClient._uses_openai_compatible_endpoint():
            return f"{model}:{provider}"
        return model

    @staticmethod
    def _uses_openai_compatible_endpoint() -> bool:
        return Settings.hf_api_url.rstrip("/").endswith("/v1/chat/completions")

    @staticmethod
    def _should_retry_request(error: Exception) -> bool:
        if isinstance(error, httpx.TimeoutException):
            return True
        if isinstance(error, httpx.TransportError):
            return True
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            return status_code == 429 or 500 <= status_code < 600
        return True

    @staticmethod
    def _fallback_reason_from_error(error: Exception) -> str:
        if isinstance(error, httpx.TimeoutException):
            return "timeout"
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            if status_code == 401:
                return "auth_failed"
            if status_code == 403:
                return "permission_denied"
            if status_code == 404:
                return "model_not_available"
            if status_code == 422:
                return "invalid_request"
            if status_code == 429:
                return "rate_limited"
            if 500 <= status_code < 600:
                return f"provider_http_{status_code}"
            return f"http_{status_code}"
        if isinstance(error, httpx.TransportError):
            return "transport_error"
        return "request_failed"

    @staticmethod
    def _should_open_circuit(error: Exception) -> bool:
        return isinstance(
            error,
            (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError),
        )

    @staticmethod
    def _response_error_log_fields(error: Exception) -> dict[str, object]:
        if not isinstance(error, httpx.HTTPStatusError):
            return {}
        response = error.response
        body = response.text.strip()
        if len(body) > 300:
            body = f"{body[:297]}..."
        return {
            "response_status_code": response.status_code,
            "response_body": body,
        }

    @staticmethod
    def _payload_log_fields(payload: dict) -> dict[str, object]:
        fields: dict[str, object] = {"kind": payload.get("kind")}
        for key in (
            "user_id",
            "track",
            "batch_number",
            "batch_size",
            "diagnostic_level",
        ):
            if key in payload:
                fields[key] = payload.get(key)
        if "mentor_focus" in payload and payload.get("mentor_focus"):
            fields["mentor_focus"] = payload.get("mentor_focus")
        if "words" in payload:
            fields["words_count"] = len(payload.get("words") or [])
        if "tasks" in payload:
            fields["tasks_count"] = len(payload.get("tasks") or [])
        return fields

    @staticmethod
    def _extract_first_choice(response_payload: object) -> Mapping[str, object]:
        if not isinstance(response_payload, Mapping):
            raise TypeError(
                f"Expected mapping response payload, got {type(response_payload).__name__}"
            )
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise KeyError("choices")
        choice = choices[0]
        if not isinstance(choice, Mapping):
            raise TypeError(f"Expected mapping choice, got {type(choice).__name__}")
        return choice

    @staticmethod
    def _extract_response_content(response_payload: object) -> str:
        choice = HuggingFaceLLMClient._extract_first_choice(response_payload)
        message = choice.get("message")
        content = HuggingFaceLLMClient._extract_choice_content(choice, message)
        if content:
            return content

        finish_reason = str(choice.get("finish_reason") or "unknown")
        reasoning_content = ""
        if isinstance(message, Mapping):
            reasoning_content = str(message.get("reasoning_content") or "").strip()
        if reasoning_content:
            raise ValueError(
                "Assistant message missing content; "
                f"finish_reason={finish_reason}; reasoning_only_response=true"
            )
        raise ValueError(
            f"Assistant message missing content; finish_reason={finish_reason}"
        )

    @staticmethod
    def _extract_choice_content(
        choice: Mapping[str, object],
        message: object,
    ) -> str:
        if isinstance(message, Mapping):
            content = HuggingFaceLLMClient._stringify_message_content(
                message.get("content")
            )
            if content:
                return content

            function_call = message.get("function_call")
            if isinstance(function_call, Mapping):
                arguments = function_call.get("arguments")
                if isinstance(arguments, str) and arguments.strip():
                    return arguments.strip()

            tool_calls = message.get("tool_calls")
            if isinstance(tool_calls, list):
                for tool_call in tool_calls:
                    if not isinstance(tool_call, Mapping):
                        continue
                    function_payload = tool_call.get("function")
                    if not isinstance(function_payload, Mapping):
                        continue
                    arguments = function_payload.get("arguments")
                    if isinstance(arguments, str) and arguments.strip():
                        return arguments.strip()

        text = choice.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        return ""

    @staticmethod
    def _stringify_message_content(content: object) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, Mapping):
            for key in ("text", "content", "value", "arguments"):
                nested = content.get(key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
            parts = content.get("parts")
            if isinstance(parts, list):
                return HuggingFaceLLMClient._stringify_message_content(parts)
            return ""
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = HuggingFaceLLMClient._stringify_message_content(item)
                if text:
                    parts.append(text)
            return "\n".join(parts).strip()
        return ""

    @staticmethod
    def _extract_json(raw_content: str):
        decoder = JSONDecoder()
        for marker in ("[", "{"):
            start = raw_content.find(marker)
            if start == -1:
                continue
            try:
                parsed, _ = decoder.raw_decode(raw_content[start:])
                return parsed
            except json.JSONDecodeError:
                continue
        raise ValueError("JSON payload was not found in model response")

    @staticmethod
    def _coerce_object(parsed: object) -> dict:
        if isinstance(parsed, Mapping):
            parsed_dict = dict(parsed)
            for key in ("response", "result", "data", "payload", "message"):
                nested = parsed_dict.get(key)
                if isinstance(nested, Mapping):
                    return dict(nested)
            return parsed_dict
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, Mapping):
                    return dict(item)
            # Если список не содержит словарей, вернём пустой dict вместо ошибки
            return {}
        if isinstance(parsed, str):
            nested = HuggingFaceLLMClient._extract_json(parsed)
            return HuggingFaceLLMClient._coerce_object(nested)
        raise TypeError(f"Expected object-like payload, got {type(parsed).__name__}")

    @staticmethod
    def _coerce_list(parsed: object) -> list:
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, Mapping):
            parsed_dict = dict(parsed)
            for key in ("cards", "items", "results", "data", "topics"):
                nested = parsed_dict.get(key)
                if isinstance(nested, list):
                    return nested
            return [parsed_dict]
        if isinstance(parsed, str):
            nested = HuggingFaceLLMClient._extract_json(parsed)
            return HuggingFaceLLMClient._coerce_list(nested)
        raise TypeError(f"Expected list-like payload, got {type(parsed).__name__}")

    @staticmethod
    def _coerce_text_list(value: object, *, limit: int) -> list[str]:
        if isinstance(value, str):
            separators = ("\n", ";", "•", "—", "-", ",")
            for separator in separators:
                if separator in value:
                    parts = [part.strip(" -—•\t") for part in value.split(separator)]
                    return [part for part in parts if part][:limit]
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()][:limit]
        return []
