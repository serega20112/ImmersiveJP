from __future__ import annotations

from src.backend.dto.knowledge_dto import KnowledgeCheckPageDTO, KnowledgeQuestionDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.profile import BuildProgressReportUseCase


class GenerateKnowledgeCheckUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        build_progress_report_use_case: BuildProgressReportUseCase,
        llm_client: HuggingFaceLLMClient,
    ):
        self._user_repository = user_repository
        self._build_progress_report_use_case = build_progress_report_use_case
        self._llm_client = llm_client

    async def execute(
        self,
        user_id: int,
        focus_area: str = "",
    ) -> KnowledgeCheckPageDTO:
        user = await self._user_repository.get_by_id(user_id)
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
