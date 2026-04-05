from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RegistrationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    password: str
    display_name: str


class VerificationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    code: str


class LoginDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str
    password: str


class UserViewDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    email: str
    display_name: str
    is_email_verified: bool
    onboarding_completed: bool
    learning_goal: str | None = None
    language_level: str | None = None
    interests: list[str] = Field(default_factory=list)


class AuthTokensDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str


class AuthResultDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    user: UserViewDTO
    tokens: AuthTokensDTO
