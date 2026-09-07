from __future__ import annotations

from src.application.dto.learning import TrackWorkResultDTO, TrackWorkTaskResultDTO
from src.application.use_cases.learning.work.submit_track_work import SubmitTrackWorkUseCase
from src.domain.aggregates.user import User
from src.domain.value_objects.track_type import TrackType
from src.tests.support import FakeUnitOfWork, build_test_card, build_test_user


class _UserRepository:
    def __init__(self, user: User):
        self._user = user

    async def get_by_id(self, user_id: int) -> User | None:
        if int(self._user.id) != user_id:
            return None
        return self._user


class _ContentRepository:
    def __init__(self, cards: list[LearningCard]):
        self.cards = cards

    async def list_cards_by_batch(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> list[LearningCard]:
        return [
            card
            for card in self.cards
            if card.user_id == user_id and card.track == track and card.batch_number == batch_number
        ]


class _ProgressRepository:
    async def is_batch_completed(
        self,
        user_id: int,
        track: TrackType,
        batch_number: int,
    ) -> bool:
        return True


class _LLMClient:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    async def review_track_work(
        self,
        *,
        user: User,
        track: TrackType,
        batch_number: int,
        tasks: list[dict[str, object]],
        fallback_result: TrackWorkResultDTO,
    ) -> TrackWorkResultDTO:
        self.calls.append(
            {
                "user_id": user.id,
                "track": track,
                "batch_number": batch_number,
                "tasks": tasks,
                "fallback_result": fallback_result,
            }
        )
        return TrackWorkResultDTO(
            score=80,
            pass_score=fallback_result.pass_score,
            passed=True,
            summary="AI проверка приняла ответы по смыслу.",
            verdict="Материал закрепился на рабочем уровне.",
            task_results=[
                TrackWorkTaskResultDTO(
                    task_id=str(task["id"]),
                    is_correct=True,
                    feedback="Ответ засчитан по смыслу.",
                )
                for task in tasks
            ],
        )


def test_submit_track_work_uses_llm_review_for_final_result():
    cards = [
        build_test_card(
            card_id=1,
            user_id=42,
            track=TrackType.HISTORY,
            topic="Реставрация Мэйдзи",
            explanation="Короткий конспект.",
            examples=["Менялись армия и школа."],
            key_terms=["Мэйдзи", "модернизация"],
            batch_number=1,
            position=1,
        ),
        build_test_card(
            card_id=2,
            user_id=42,
            track=TrackType.HISTORY,
            topic="Эдо как городской порядок",
            explanation="Короткий конспект.",
            examples=["Коммерция влияла на быт."],
            key_terms=["Эдо", "город"],
            batch_number=1,
            position=2,
        ),
        build_test_card(
            card_id=3,
            user_id=42,
            track=TrackType.HISTORY,
            topic="Память о войне",
            explanation="Короткий конспект.",
            examples=["Тема остается живой."],
            key_terms=["память", "война"],
            batch_number=1,
            position=3,
        ),
    ]
    llm_client = _LLMClient()
    use_case = SubmitTrackWorkUseCase(
        FakeUnitOfWork(
            {
                "user": _UserRepository(build_test_user(user_id=42, interests=["история"])),
                "content": _ContentRepository(cards),
                "progress": _ProgressRepository(),
            }
        ),
        llm_client,
    )

    result = __import__("asyncio").run(
        use_case.execute(
            42,
            TrackType.HISTORY,
            1,
            {
                "thesis": "Реформы Мэйдзи ускорили модернизацию государства.",
                "context": "В Эдо городской порядок держался на плотной повседневности.",
                "meaning": "Память о войне влияет на современный взгляд на прошлое.",
                "scene": "После перелома менялись институты и городская среда.",
                "confidence": "История соединяет реформы, город и память о войне.",
            },
        )
    )

    assert llm_client.calls
    assert result.result is not None
    assert result.result.score == 80
    assert result.result.passed is True
    assert result.result.summary == "AI проверка приняла ответы по смыслу."
