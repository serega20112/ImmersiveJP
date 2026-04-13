from __future__ import annotations

from src.backend.domain.content import TrackType
from src.backend.domain.user import LanguageLevel, SkillAssessment
from src.backend.dto.onboarding_dto import OnboardingDTO
from src.backend.use_case.onboarding.complete_onboarding import CompleteOnboardingUseCase


class _RecordingUserRepository:
    def __init__(self):
        self.updated_payload: dict[str, object] | None = None

    async def update_learning_profile(self, **payload):
        self.updated_payload = payload


class _RecordingGenerateCardsUseCase:
    def __init__(self):
        self.tracks: list[TrackType] = []

    async def execute(self, user_id: int, track: TrackType):
        self.tracks.append(track)
        return []


def test_complete_onboarding_generates_only_language_track(monkeypatch):
    user_repository = _RecordingUserRepository()
    generate_cards_use_case = _RecordingGenerateCardsUseCase()
    use_case = CompleteOnboardingUseCase(user_repository, generate_cards_use_case)

    monkeypatch.setattr(
        "src.backend.use_case.onboarding.complete_onboarding.evaluate_diagnostic_answers",
        lambda answers, language_level, hints_used: SkillAssessment(
            score=67,
            estimated_level=LanguageLevel.BASIC,
            summary="Базовый уровень держится, но есть просадки в частицах.",
            strengths=["Лексика"],
            weak_points=["Частицы"],
        ),
    )

    result = __import__("asyncio").run(
        use_case.execute(
            42,
            OnboardingDTO(
                goal="tourism",
                language_level="basic",
                study_timeline="six_months",
                interests_text="еда, поездки",
                diagnostic_answers={"q1": "a"},
                diagnostic_hints_used=0,
            ),
        )
    )

    assert generate_cards_use_case.tracks == [TrackType.LANGUAGE]
    assert result.generated_batches == {"language": 1}
