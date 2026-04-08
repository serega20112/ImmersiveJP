from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MentorMessageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: str
    content: str
    created_at_label: str
    action_steps: list[str] = Field(default_factory=list)


class MentorFocusDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    title: str
    note: str
    track: str


class MentorReplyDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    reply: str
    action_steps: list[str] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)


class MentorPageDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    subtitle: str
    next_step: str
    current_stage_title: str
    pace_title: str
    content_mode_title: str
    active_focus: MentorFocusDTO | None = None
    messages: list[MentorMessageDTO] = Field(default_factory=list)
    suggested_prompts: list[str] = Field(default_factory=list)
    draft_message: str = ""
