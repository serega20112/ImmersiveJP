from __future__ import annotations

from src.application.dto.profile import AIAdviceDTO, ProgressReportDTO
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import LLMClient


class GenerateAIAdviceUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        llm_client: LLMClient,
    ):
        """Initialize the generate AI advice use case.

        Args:
            uow: Unit of work for database transactions.
            llm_client: Client for LLM chat completions.
        """
        self._uow = uow
        self._llm_client = llm_client

    async def execute(self, user_id: int, report: ProgressReportDTO) -> AIAdviceDTO:
        """Generate AI advice based on a progress report.

        Args:
            user_id: ID of the user.
            report: The progress report to base advice on.

        Returns:
            The generated AI advice.

        Raises:
            ValueError: If the user is not found.
        """
        async with self._uow as uow:
            user_repository = uow.users
            user = await user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        return await self._llm_client.generate_advice(user, report)
