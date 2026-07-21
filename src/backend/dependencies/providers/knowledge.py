from __future__ import annotations

from functools import cached_property

from src.backend.use_case.knowledge import (
    GenerateKnowledgeCheckUseCase,
    SubmitKnowledgeCheckUseCase,
)


class KnowledgeProvidersMixin:
    @cached_property
    def generate_knowledge_check_use_case(self) -> GenerateKnowledgeCheckUseCase:
        return GenerateKnowledgeCheckUseCase(
            self.user_repository,
            self.build_progress_report_use_case,
            self.root.llm_client,
        )

    @cached_property
    def submit_knowledge_check_use_case(self) -> SubmitKnowledgeCheckUseCase:
        return SubmitKnowledgeCheckUseCase(self.root.llm_client)
