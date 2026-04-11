from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from src.backend.domain.content import TrackType
from src.backend.domain.user import LanguageLevel, LearningGoal, StudyTimeline, User
from src.backend.dto.learning import GeneratedCardDraftDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient


@dataclass
class DummyStore:
    payloads: dict[str, object] = field(default_factory=dict)

    async def get_json(self, key: str):
        return self.payloads.get(key)

    async def set_json(self, key: str, value: object, expire_seconds: int):
        self.payloads[key] = value

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
