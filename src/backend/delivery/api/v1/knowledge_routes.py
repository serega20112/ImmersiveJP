from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request

from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.service_dependencies import KnowledgeServiceDependency
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.dto.knowledge_dto import KnowledgeQuestionDTO
from src.backend.infrastructure.web import flash, render_template

knowledge_router = APIRouter(prefix="/check")


@knowledge_router.get("", name="knowledge.page")
async def knowledge_page(
    request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
):
    """Render the knowledge check page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.

    Returns:
        The rendered knowledge template.
    """
    return await render_template(request, "knowledge/index.html")


@knowledge_router.post("/generate", name="knowledge.generate")
async def knowledge_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    knowledge_service: KnowledgeServiceDependency,
    focus_area: str = Form(""),
):
    """Handle knowledge check generation.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        knowledge_service: The knowledge service dependency.
        focus_area: Optional focus area for questions.

    Returns:
        The rendered knowledge template with questions.
    """
    page = await knowledge_service.generate_check(current_user.id, focus_area)
    if not page.questions:
        flash(request, "Не удалось сгенерировать вопросы. Попробуй ещё раз.", "error")
        return redirect_to_route(request, "knowledge.page")
    page_dict = page.model_dump()
    page_dict["questions_json"] = json.dumps(
        [q.model_dump() for q in page.questions], ensure_ascii=False
    )
    return await render_template(request, "knowledge/index.html", page=page_dict)


@knowledge_router.post("/submit", name="knowledge.submit")
async def knowledge_submit(
    request: Request,
    _current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    knowledge_service: KnowledgeServiceDependency,
):
    """Handle knowledge check submission.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        knowledge_service: The knowledge service dependency.

    Returns:
        The rendered knowledge template with results.
    """
    form = await request.form()
    questions_json = form.get("questions_json", "")
    try:
        raw_questions = json.loads(str(questions_json))
    except (json.JSONDecodeError, ValueError):
        flash(request, "Ошибка данных. Сгенерируй новый тест.", "error")
        return redirect_to_route(request, "knowledge.page")

    questions = [KnowledgeQuestionDTO(**q) for q in raw_questions]
    answers = {
        key.removeprefix("answer_"): str(value)
        for key, value in form.items()
        if key.startswith("answer_")
    }
    page = await knowledge_service.submit_check(questions, answers)
    page_dict = page.model_dump()
    page_dict["questions_json"] = json.dumps(
        [q.model_dump() for q in page.questions], ensure_ascii=False
    )
    return await render_template(request, "knowledge/index.html", page=page_dict)
