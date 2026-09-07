from __future__ import annotations

from src.application.dto.onboarding import OnboardingDTO
from src.application.use_cases.onboarding.complete_onboarding import (
    CompleteOnboardingUseCase,
)
from src.domain.aggregates.user import User
from src.domain.value_objects.skill_assessment import SkillAssessment
from src.domain.value_objects.track_type import TrackType
from src.domain.value_objects.user import LanguageLevel
from src.tests.support import FakeUnitOfWork, build_test_user


class _RecordingUserRepository:
    def __init__(self, user: User):
        self._user = user
        self.saved_user: User | None = None

    async def get_by_id(self, user_id: int) -> User | None:
        if int(self._user.id or 0) != user_id:
            return None
        return self._user

    async def save(self, user: User) -> User:
        self.saved_user = user
        self._user = user
        return user


class _RecordingGenerateCardsUseCase:
    def __init__(self):
        self.tracks: list[TrackType] = []

    async def execute(self, user_id: int, track: TrackType):
        self.tracks.append(track)
        return []


def test_complete_onboarding_generates_only_language_track(monkeypatch):
    user = build_test_user(user_id=42, onboarding_completed=False)
    user_repository = _RecordingUserRepository(user)
    generate_cards_use_case = _RecordingGenerateCardsUseCase()
    use_case = CompleteOnboardingUseCase(
        FakeUnitOfWork({"user": user_repository}),
        generate_cards_use_case,
    )

    monkeypatch.setattr(
        "src.application.use_cases.onboarding.complete_onboarding.evaluate_diagnostic_answers",
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
    assert user_repository.saved_user is not None
    assert user_repository.saved_user.onboarding_completed is True
