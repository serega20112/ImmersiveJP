from __future__ import annotations

from src.backend.domain.mentor import MentorFocus, MentorMessage
from src.backend.dto.mentor_dto import MentorFocusDTO, MentorMessageDTO, MentorPageDTO
from src.backend.infrastructure.repositories import AbstractMentorRepository
from src.backend.use_case.profile.build_learning_plan import BuildLearningPlanUseCase
from src.backend.use_case.profile.build_progress_report import (
    BuildProgressReportUseCase,
)


class GetMentorPageUseCase:
    def __init__(
        self,
        mentor_repository: AbstractMentorRepository,
        build_progress_report_use_case: BuildProgressReportUseCase,
        build_learning_plan_use_case: BuildLearningPlanUseCase,
    ):
        self._mentor_repository = mentor_repository
        self._build_progress_report_use_case = build_progress_report_use_case
        self._build_learning_plan_use_case = build_learning_plan_use_case

    async def execute(self, user_id: int, draft_message: str = "") -> MentorPageDTO:
        report = await self._build_progress_report_use_case.execute(user_id)
        plan = await self._build_learning_plan_use_case.execute(user_id)
        history = await self._mentor_repository.get_messages(user_id)
        active_focus = await self._mentor_repository.get_focus(user_id)
        return MentorPageDTO(
            title="Наставник",
            subtitle="Здесь можно менять фокус обучения без хаотичных прыжков по темам. Наставник смотрит на текущий план, прогресс и слабые места.",
            next_step=report.next_step,
            current_stage_title=plan.current_stage_title,
            pace_title=plan.pace_mode.title,
            content_mode_title=plan.content_mode.title,
            active_focus=self._to_focus_dto(active_focus),
            messages=[self._to_message_dto(message) for message in history],
            suggested_prompts=self._suggested_prompts(active_focus),
            draft_message=draft_message,
        )

    @staticmethod
    def _to_message_dto(message: MentorMessage) -> MentorMessageDTO:
        return MentorMessageDTO(
            role=message.role,
            content=message.content,
            created_at_label=message.created_at.strftime("%H:%M"),
            action_steps=list(message.action_steps),
        )

    @staticmethod
    def _to_focus_dto(focus: MentorFocus | None) -> MentorFocusDTO | None:
        if focus is None:
            return None
        return MentorFocusDTO(
            key=focus.key,
            title=focus.title,
            note=focus.note,
            track=focus.track,
        )

    @staticmethod
    def _suggested_prompts(active_focus: MentorFocus | None) -> list[str]:
        prompts = [
            "Я в кандзи сильно проседаю, что сейчас делать?",
            "У меня частицы путаются. Как лучше это добить по плану?",
            "Можно ускорить разговорную практику без пропуска базы?",
        ]
        if active_focus is not None:
            prompts.insert(0, f"Как двигаться дальше с фокусом: {active_focus.title}?")
        return prompts[:4]
