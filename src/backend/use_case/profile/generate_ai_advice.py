from __future__ import annotations

from src.backend.dto.profile_dto import AIAdviceDTO, ProgressReportDTO
from src.backend.infrastructure.external import HuggingFaceLLMClient
from src.backend.infrastructure.repositories import AbstractUserRepository


class GenerateAIAdviceUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        llm_client: HuggingFaceLLMClient,
    ):
        self._user_repository = user_repository
        self._llm_client = llm_client

    async def execute(self, user_id: int, report: ProgressReportDTO) -> AIAdviceDTO:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")
        return await self._llm_client.generate_advice(user, report)
