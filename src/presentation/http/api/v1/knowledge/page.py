"""Роут страницы проверки знаний."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.presentation.http import render_template

knowledge_page_router = APIRouter()


@knowledge_page_router.get("/", name="knowledge.page")
async def knowledge_page(
    request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
) -> HTMLResponse:
    """Отрисовать страницу проверки знаний.

    Args:
        request: Входящий запрос.
        _current_user: Авторизованный пользователь с онбордингом.

    Returns:
        Ответ с шаблоном проверки знаний.
    """
    return await render_template(request, "knowledge/index.html")
