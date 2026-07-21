from __future__ import annotations

from src.backend.dto.knowledge_dto import KnowledgeCheckPageDTO, KnowledgeQuestionDTO
from src.backend.use_case.knowledge import (
    GenerateKnowledgeCheckUseCase,
    SubmitKnowledgeCheckUseCase,
)


class KnowledgeService:
    def __init__(
        self,
        generate_knowledge_check_use_case: GenerateKnowledgeCheckUseCase,
        submit_knowledge_check_use_case: SubmitKnowledgeCheckUseCase,
    ):
        """Initialize the knowledge service.

        Args:
            generate_knowledge_check_use_case: Use case for generating knowledge checks.
            submit_knowledge_check_use_case: Use case for submitting knowledge checks.
        """
        self._generate_knowledge_check_use_case = generate_knowledge_check_use_case
        self._submit_knowledge_check_use_case = submit_knowledge_check_use_case

    async def generate_check(
        self,
        user_id: int,
        focus_area: str = "",
    ) -> KnowledgeCheckPageDTO:
        """Generate a knowledge check for the user.

        Args:
            user_id: ID of the user.
            focus_area: Optional area to focus questions on.

        Returns:
            The knowledge check page with questions.
        """
        return await self._generate_knowledge_check_use_case.execute(user_id, focus_area)

    async def submit_check(
        self,
        questions: list[KnowledgeQuestionDTO],
        answers: dict[str, str],
    ) -> KnowledgeCheckPageDTO:
        """Submit a knowledge check and get evaluation results.

        Args:
            questions: The list of knowledge check questions.
            answers: Dictionary of question ID to answer text.

        Returns:
            The knowledge check page with results.
        """
        return await self._submit_knowledge_check_use_case.execute(questions, answers)
