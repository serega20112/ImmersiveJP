from __future__ import annotations

from src.backend.dto.knowledge_dto import (
    KnowledgeAnswerResultDTO,
    KnowledgeCheckPageDTO,
    KnowledgeQuestionDTO,
)
from src.backend.infrastructure.external import HuggingFaceLLMClient


class SubmitKnowledgeCheckUseCase:
    def __init__(
        self,
        llm_client: HuggingFaceLLMClient,
    ):
        self._llm_client = llm_client

    async def execute(
        self,
        questions: list[KnowledgeQuestionDTO],
        answers: dict[str, str],
    ) -> KnowledgeCheckPageDTO:
        questions_raw = [
            {
                "id": q.id,
                "kind": q.kind,
                "question": q.question,
                "context": q.context,
                "expected_answer": "",
                "hints": list(q.hints),
            }
            for q in questions
        ]

        result = await self._llm_client.evaluate_knowledge_check(
            user_id=0,
            questions=questions_raw,
            answers=answers,
        )

        score = result.get("score", 0)
        summary = result.get("summary", "")
        raw_results = result.get("results", [])

        results = [
            KnowledgeAnswerResultDTO(
                question_id=r["question_id"],
                is_correct=r["is_correct"],
                user_answer=r.get("user_answer", ""),
                expected_answer=r.get("expected_answer", ""),
                feedback=r.get("feedback", ""),
            )
            for r in raw_results
        ]

        return KnowledgeCheckPageDTO(
            title="Проверка знаний",
            subtitle="Результат",
            focus_area="",
            questions=questions,
            results=results,
            score=score,
            summary=summary,
            passed=score >= 60,
        )
