"""DTO аутентификации: регистрация, вход, подтверждение почты, токены."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RegistrationDTO(BaseModel):
    """Данные нового пользователя при регистрации.

    Атрибуты:
        email: Адрес электронной почты.
        password: Пароль пользователя.
        display_name: Отображаемое имя пользователя.
    """

    model_config = ConfigDict(frozen=True)

    email: str
    password: str
    display_name: str


class VerificationDTO(BaseModel):
    """Данные для подтверждения адреса электронной почты.

    Атрибуты:
        email: Адрес электронной почты.
        code: Код подтверждения из письма.
    """

    model_config = ConfigDict(frozen=True)

    email: str
    code: str


class LoginDTO(BaseModel):
    """Учётные данные для входа.

    Атрибуты:
        email: Адрес электронной почты.
        password: Пароль пользователя.
    """

    model_config = ConfigDict(frozen=True)

    email: str
    password: str


class UserViewDTO(BaseModel):
    """Публичное представление пользователя.

    Атрибуты:
        id: Идентификатор пользователя.
        email: Адрес электронной почты.
        display_name: Отображаемое имя пользователя.
        is_email_verified: Флаг подтверждения почты.
        onboarding_completed: Флаг завершения онбординга.
        learning_goal: Цель обучения.
        language_level: Уровень языка.
        study_timeline: Желаемый срок обучения.
        interests: Список интересов пользователя.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    email: str
    display_name: str
    is_email_verified: bool
    onboarding_completed: bool
    learning_goal: str | None = None
    language_level: str | None = None
    study_timeline: str | None = None
    interests: list[str] = Field(default_factory=list)


class AuthTokensDTO(BaseModel):
    """Пара токенов доступа.

    Атрибуты:
        access_token: Короткоживущий токен доступа.
        refresh_token: Долгоживущий токен обновления.
    """

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str


class AuthResultDTO(BaseModel):
    """Результат успешной аутентификации.

    Атрибуты:
        user: Публичное представление пользователя.
        tokens: Пара токенов доступа.
    """

    model_config = ConfigDict(frozen=True)

    user: UserViewDTO
    tokens: AuthTokensDTO
