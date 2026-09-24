from __future__ import annotations

from src.application.dto.knowledge import KnowledgeCheckPageDTO, KnowledgeQuestionDTO
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient
from src.application.use_cases.profile import BuildProgressReportUseCase


class GenerateKnowledgeCheckUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        build_progress_report_use_case: BuildProgressReportUseCase,
        llm_client: LLMClient,
    ):
        """Initialize the generate knowledge check use case.

        Args:
            uow: Unit of work for database transactions.
            build_progress_report_use_case: Use case for building progress reports.
            llm_client: Client for LLM chat completions.
        """
        self._uow = uow
        self._build_progress_report_use_case = build_progress_report_use_case
        self._llm_client = llm_client

    async def execute(
        self,
        user_id: int,
        focus_area: str = "",
    ) -> KnowledgeCheckPageDTO:
        """Generate a knowledge check with questions for a user.

        Args:
            user_id: ID of the user.
            focus_area: Optional area to focus questions on.

        Returns:
            The knowledge check page with questions.

        Raises:
            ValueError: If the user is not found.
        """
        async with self._uow as uow:
            user_repository = uow.users
            user = await user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        report = await self._build_progress_report_use_case.execute(user_id)
        skill = report.skill_assessment

        raw_questions = await self._llm_client.generate_knowledge_check(
            user=user,
            weak_points=list(skill.weak_points) if skill else None,
            strengths=list(skill.strengths) if skill else None,
            recent_topics=None,
            focus_area=focus_area,
        )

        questions = [
            KnowledgeQuestionDTO(
                id=q["id"],
                kind=q["kind"],
                question=q["question"],
                context=q.get("context", ""),
                hints=list(q.get("hints", [])),
            )
            for q in raw_questions
        ]

        return KnowledgeCheckPageDTO(
            title="Проверка знаний",
            subtitle="Ответь на вопросы, чтобы закрепить материал",
            focus_area=focus_area or "общая",
            questions=questions,
        )
