from __future__ import annotations

from dataclasses import dataclass, field

import httpx
import pytest

from src.backend.domain.content import TrackType
from src.backend.domain.user import LanguageLevel, LearningGoal, StudyTimeline, User
from src.backend.dto.learning import (
    GeneratedCardDraftDTO,
    TrackWorkResultDTO,
    TrackWorkTaskResultDTO,
)
from src.backend.infrastructure.external import HuggingFaceLLMClient


@dataclass
class DummyStore:
    payloads: dict[str, object] = field(default_factory=dict)

    async def get_json(self, key: str):
        return self.payloads.get(key)

    async def set_json(self, key: str, value: object, expire_seconds: int):
        self.payloads[key] = value

    async def delete(self, key: str):
        self.payloads.pop(key, None)

    async def close(self):
        return None


def _build_user() -> User:
    return User(
        id=1,
        email="user@example.com",
        password_hash="hashed",
        display_name="Immers User",
        is_email_verified=True,
        learning_goal=LearningGoal.TOURISM,
        language_level=LanguageLevel.BASIC,
        study_timeline=StudyTimeline.SIX_MONTHS,
        interests=["еда", "поездки"],
        onboarding_completed=True,
    )


@pytest.mark.asyncio
async def test_generate_cards_uses_cache_and_keeps_public_api():
    store = DummyStore()
    client = HuggingFaceLLMClient(store)
    user = _build_user()
    calls: list[dict[str, object]] = []

    async def fake_request(payload: dict):
        calls.append(payload)
        return [
            GeneratedCardDraftDTO(
                topic="Приветствие в поезде",
                explanation="Короткий конспект о фразах в транспорте.",
                examples=[
                    "すみません。 | sumimasen. | Извините.",
                    "ここです。 | koko desu. | Вот здесь.",
                    "ありがとうございます。 | arigatou gozaimasu. | Спасибо.",
                ],
                key_terms=["挨拶 | приветствие", "電車 | поезд"],
            )
        ]

    client._request_cards = fake_request  # type: ignore[method-assign]

    first = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=1,
        batch_size=1,
        previous_topics=[],
    )
    second = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=1,
        batch_size=1,
        previous_topics=[],
    )

    await client.close()

    assert len(calls) == 1
    assert first[0].topic == "Приветствие в поезде"
    assert second[0].topic == first[0].topic
    assert store.payloads


def test_split_llm_modules_keep_cross_module_static_calls_working():
    prompt = HuggingFaceLLMClient._build_cards_prompt(
        {
            "track": "language",
            "goal": "tourism",
            "language_level": "basic",
            "study_timeline": "six_months",
            "interests": ["еда"],
            "batch_number": 2,
            "batch_size": 3,
            "previous_topics": ["Приветствия"],
            "weak_points": [],
            "strengths": [],
            "mentor_focus": None,
            "diagnostic_level": "basic",
        }
    )

    fallback = HuggingFaceLLMClient._fallback_speech_practice(
        {
            "words": ["日本語 | nihongo | японский язык"],
            "language_level": "basic",
            "study_timeline": "six_months",
            "weak_points": [],
        }
    )

    assert "Сгенерируй карточки-конспекты по Японии." in prompt
    assert fallback.sentences
    assert fallback.dialogues


def test_cards_runtime_uses_dedicated_settings(monkeypatch: pytest.MonkeyPatch):
    from src.backend.dependencies.settings import Settings

    monkeypatch.setattr(Settings, "hf_cards_model", "openai/gpt-oss-20b")
    monkeypatch.setattr(Settings, "hf_cards_timeout_seconds", 10.0)
    monkeypatch.setattr(Settings, "hf_cards_retry_attempts", 1)
    monkeypatch.setattr(Settings, "hf_cards_max_tokens", 1400)
    monkeypatch.setattr(Settings, "hf_provider", "fireworks-ai")

    model, timeout_seconds, retry_attempts, max_tokens = (
        HuggingFaceLLMClient._request_runtime({"kind": "cards"})
    )

    assert model == "openai/gpt-oss-20b:fireworks-ai"
    assert timeout_seconds == 10.0
    assert retry_attempts == 1
    assert max_tokens == 1400


@pytest.mark.asyncio
async def test_cards_circuit_breaker_skips_remote_request_after_timeout(
    monkeypatch: pytest.MonkeyPatch,
):
    from src.backend.dependencies.settings import Settings

    store = DummyStore()
    client = HuggingFaceLLMClient(store)
    user = _build_user()
    request_calls = 0

    monkeypatch.setattr(Settings, "hf_api_token", "test-token")
    monkeypatch.setattr(Settings, "hf_cards_circuit_open_seconds", 900)

    async def failing_request(*, payload, temperature, system_content, user_content):
        nonlocal request_calls
        request_calls += 1
        raise httpx.ReadTimeout(
            "timed out",
            request=httpx.Request("POST", "https://router.huggingface.co/v1/chat/completions"),
        )

    client._request_llm_json = failing_request  # type: ignore[method-assign]

    first = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=1,
        batch_size=1,
        previous_topics=[],
    )
    second = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=2,
        batch_size=1,
        previous_topics=["Приветствия"],
    )

    await client.close()

    assert request_calls == 1
    assert len(first) == 1
    assert len(second) == 1


@pytest.mark.asyncio
async def test_timeout_circuit_allows_retry_for_smaller_batch_size(
    monkeypatch: pytest.MonkeyPatch,
):
    from src.backend.dependencies.settings import Settings

    store = DummyStore()
    client = HuggingFaceLLMClient(store)
    user = _build_user()
    request_calls = 0

    monkeypatch.setattr(Settings, "hf_api_token", "test-token")
    monkeypatch.setattr(Settings, "hf_cards_circuit_open_seconds", 900)

    async def first_timeout_then_success(
        *,
        payload,
        temperature,
        system_content,
        user_content,
    ):
        nonlocal request_calls
        request_calls += 1
        if request_calls == 1:
            raise httpx.ReadTimeout(
                "timed out",
                request=httpx.Request(
                    "POST",
                    "https://router.huggingface.co/v1/chat/completions",
                ),
            )
        return [
            {
                "topic": "Поиск платформы",
                "explanation": "Короткий конспект о том, как уточнять путь.",
                "examples": [
                    "何番線ですか。 | nanbansen desu ka. | Какая платформа?",
                    "ここで待ちます。 | koko de machimasu. | Я подожду здесь.",
                    "電車は何時ですか。 | densha wa nanji desu ka. | Во сколько поезд?",
                ],
                "key_terms": ["番線 | платформа", "電車 | поезд"],
            }
        ]

    client._request_llm_json = first_timeout_then_success  # type: ignore[method-assign]

    first = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=1,
        batch_size=3,
        previous_topics=[],
    )
    second = await client.generate_cards(
        user=user,
        track=TrackType.LANGUAGE,
        batch_number=2,
        batch_size=1,
        previous_topics=["Приветствия"],
    )

    await client.close()

    assert request_calls == 2
    assert len(first) == 3
    assert len(second) == 1
    assert second[0].topic == "Поиск платформы"


def test_normalize_cards_replaces_history_offtopic_with_history_fallback():
    payload = {
        "track": "history",
        "batch_size": 1,
        "previous_topics": [],
        "interests": ["переезд"],
    }

    normalized = HuggingFaceLLMClient._normalize_cards(
        [
            {
                "topic": "Виза для переезда",
                "explanation": "Как собрать документы на визу, снять жилье и оформить бытовые шаги.",
                "examples": [
                    "Подай документы заранее.",
                    "Проверь аренду квартиры.",
                    "Собери визовый пакет.",
                ],
                "key_terms": ["виза", "аренда", "документы"],
            }
        ],
        payload,
    )

    assert len(normalized) == 1
    assert normalized[0].topic != "Виза для переезда"
    assert "виза" not in normalized[0].topic.casefold()


@pytest.mark.asyncio
async def test_review_track_work_uses_llm_result_with_fallback_shape(
    monkeypatch: pytest.MonkeyPatch,
):
    from src.backend.dependencies.settings import Settings

    store = DummyStore()
    client = HuggingFaceLLMClient(store)
    user = _build_user()

    monkeypatch.setattr(Settings, "hf_api_token", "test-token")

    async def fake_request(*, payload, temperature, system_content, user_content):
        return {
            "summary": "По партии смысл в целом держится.",
            "verdict": "Материал частично закрепился, но есть пробелы.",
            "task_results": [
                {
                    "task_id": "thesis",
                    "is_correct": True,
                    "feedback": "Смысл темы передан по делу.",
                },
                {
                    "task_id": "context",
                    "is_correct": False,
                    "feedback": "Ответ слишком общий и не привязан к материалу партии.",
                },
            ],
        }

    client._request_llm_json = fake_request  # type: ignore[method-assign]

    reviewed = await client.review_track_work(
        user=user,
        track=TrackType.HISTORY,
        batch_number=2,
        tasks=[
            {
                "id": "thesis",
                "kind": "production",
                "prompt": "Коротко объясни тему.",
                "answer": "Это связано с реформами Мэйдзи.",
                "required_terms": ["Мэйдзи", "реформы"],
                "expected_answers": [],
            },
            {
                "id": "context",
                "kind": "production",
                "prompt": "Покажи контекст.",
                "answer": "Это было важно.",
                "required_terms": ["государство", "модернизация"],
                "expected_answers": [],
            },
        ],
        fallback_result=TrackWorkResultDTO(
            score=0,
            pass_score=80,
            passed=False,
            summary="fallback",
            verdict="fallback",
            task_results=[
                TrackWorkTaskResultDTO(
                    task_id="thesis",
                    is_correct=False,
                    feedback="fallback thesis",
                    revealed_answer="Мэйдзи, реформы",
                ),
                TrackWorkTaskResultDTO(
                    task_id="context",
                    is_correct=False,
                    feedback="fallback context",
                    revealed_answer="государство, модернизация",
                ),
            ],
        ),
    )

    await client.close()

    assert reviewed.score == 50
    assert reviewed.passed is False
    assert reviewed.summary == "По партии смысл в целом держится."
    assert reviewed.task_results[0].is_correct is True
    assert reviewed.task_results[1].feedback.startswith("Ответ слишком общий")
