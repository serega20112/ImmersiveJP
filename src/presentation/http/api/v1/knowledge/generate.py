"""Роут генерации проверки знаний."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import KnowledgeServiceDependency
from src.presentation.http import RouteRedirectError, flash, render_template
from src.presentation.http.schemas import KnowledgeGenerateForm

knowledge_generate_router = APIRouter()


@knowledge_generate_router.post("/generate", name="knowledge.generate")
async def knowledge_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    knowledge_service: KnowledgeServiceDependency,
    form: Annotated[KnowledgeGenerateForm, Depends()],
) -> HTMLResponse:
    """Обработать генерацию вопросов для проверки знаний.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        knowledge_service: Сервис проверки знаний.
        form: Параметры генерации вопросов.

    Returns:
        Ответ с шаблоном проверки знаний и вопросами.
    """
    page = await knowledge_service.generate_check(current_user.id, form.focus_area)
    if not page.questions:
        flash(request, "Не удалось сгенерировать вопросы. Попробуйте ещё раз.", "error")
        raise RouteRedirectError(request.app.url_path_for("knowledge.page"))
    page_dict = page.model_dump()
    page_dict["questions_json"] = json.dumps(
        [q.model_dump() for q in page.questions], ensure_ascii=False
    )
    return await render_template(request, "knowledge/index.html", page=page_dict)
