from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OnboardingDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    goal: str
    language_level: str
    interests_text: str


class OnboardingResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_id: int
    generated_batches: dict[str, int]
