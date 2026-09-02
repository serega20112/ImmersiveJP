from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeQuestionDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: str
    question: str
    context: str = ""
    hints: list[str] = Field(default_factory=list)


class KnowledgeAnswerResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_id: str
    is_correct: bool
    user_answer: str
    expected_answer: str
    feedback: str


class KnowledgeCheckPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    focus_area: str
    questions: list[KnowledgeQuestionDTO] = Field(default_factory=list)
    results: list[KnowledgeAnswerResultDTO] | None = None
    score: int | None = None
    summary: str | None = None
    passed: bool | None = None
