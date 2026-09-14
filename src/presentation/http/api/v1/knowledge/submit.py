"""Роут отправки ответов проверки знаний."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.application.dto.knowledge import KnowledgeQuestionDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import KnowledgeServiceDependency
from src.presentation.http import render_template
from src.presentation.http.schemas import KnowledgeSubmitForm

knowledge_submit_router = APIRouter()


@knowledge_submit_router.post("/submit", name="knowledge.submit")
async def knowledge_submit(
    request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    knowledge_service: KnowledgeServiceDependency,
    form: Annotated[KnowledgeSubmitForm, Form()],
) -> HTMLResponse:
    """Обработать отправку ответов на проверку знаний.

    Args:
        request: Входящий запрос.
        _current_user: Авторизованный пользователь с онбордингом.
        knowledge_service: Сервис проверки знаний.
        form: Данные формы отправки ответов.

    Returns:
        Ответ с шаблоном проверки знаний и результатами.

    Ошибки разбора данных теста обрабатываются глобальными обработчиками.
    """
    raw_form = await request.form()
    questions = KnowledgeQuestionDTO.list_from_json(form.questions_json)
    answers = {
        key.removeprefix("answer_"): str(value)
        for key, value in raw_form.items()
        if key.startswith("answer_")
    }
    page = await knowledge_service.submit_check(questions, answers)
    page_dict = page.model_dump()
    page_dict["questions_json"] = json.dumps(
        [q.model_dump() for q in page.questions], ensure_ascii=False
    )
    return await render_template(request, "knowledge/index.html", page=page_dict)
