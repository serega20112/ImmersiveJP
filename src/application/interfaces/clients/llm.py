"""Порт LLM-клиента для генерации учебного контента."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from src.application.dto.learning import (
    GeneratedCardDraftDTO,
    SpeechPracticeDTO,
    TrackWorkResultDTO,
)
from src.application.dto.mentor import MentorReplyDTO
from src.application.dto.profile import AIAdviceDTO, LearningPlanPageDTO, ProgressReportDTO
from src.domain.aggregates.user import User
from src.domain.value_objects.track_type import TrackType


@runtime_checkable
class LLMClient(Protocol):
    """Порт LLM-клиента для генерации учебного контента."""

    async def generate_cards(
        self,
        user: User,
        track: TrackType,
        batch_number: int,
        batch_size: int,
        previous_topics: list[str],
        mentor_focus: str | None = None,
    ) -> list[GeneratedCardDraftDTO]:
        """Сгенерировать черновики карточек для нового батча."""
        pass

    async def generate_advice(self, user: User, report: ProgressReportDTO) -> AIAdviceDTO:
        """Сгенерировать персональный совет по прогрессу."""
        pass

    async def generate_speech_practice(
        self,
        user: User,
        words: list[str],
    ) -> SpeechPracticeDTO:
        """Сгенерировать упражнение на отработку слов."""
        pass

    async def generate_mentor_reply(
        self,
        *,
        user: User,
        report: ProgressReportDTO,
        plan: LearningPlanPageDTO,
        message: str,
    ) -> MentorReplyDTO:
        """Сгенерировать ответ ментора на сообщение пользователя."""
        pass

    async def generate_knowledge_check(
        self,
        *,
        user: User,
        weak_points: list[str] | None = None,
        strengths: list[str] | None = None,
        recent_topics: list[str] | None = None,
        focus_area: str = "",
    ) -> list[dict[str, Any]]:
        """Сгенерировать вопросы для проверки знаний."""
        pass

    async def evaluate_knowledge_check(
        self,
        *,
        user_id: int = 0,
        questions: list[dict[str, Any]],
        answers: dict[str, str],
    ) -> dict[str, Any]:
        """Оценить ответы пользователя на вопросы проверки."""
        pass

    async def review_track_work(
        self,
        *,
        user: User,
        track: TrackType,
        batch_number: int,
        tasks: list[dict[str, object]],
        answers: dict[str, str],
    ) -> TrackWorkResultDTO:
        """Проверить домашнюю работу по треку."""
        pass

    async def close(self) -> None:
        """Освободить ресурсы клиента."""
        pass
