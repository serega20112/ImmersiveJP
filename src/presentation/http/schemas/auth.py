"""Схемы форм аутентификации."""

from __future__ import annotations

from fastapi import Form
from pydantic import BaseModel


class LoginForm(BaseModel):
    """Форма входа.

    Атрибуты:
        email: Email пользователя.
        password: Пароль пользователя.
    """

    email: str = Form()
    password: str = Form()


class RegistrationForm(BaseModel):
    """Форма регистрации.

    Атрибуты:
        email: Email пользователя.
        password: Пароль пользователя.
        display_name: Отображаемое имя пользователя.
    """

    email: str = Form()
    password: str = Form()
    display_name: str = Form()


class VerificationForm(BaseModel):
    """Форма подтверждения email.

    Атрибуты:
        email: Email пользователя.
        code: Код подтверждения из письма.
    """

    email: str = Form()
    code: str = Form()
