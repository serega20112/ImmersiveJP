from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request

from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.request_scope import get_request_container
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.dto.knowledge_dto import KnowledgeQuestionDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template

knowledge_router = APIRouter(prefix="/check")


@knowledge_router.get("", name="knowledge.page")
async def knowledge_page(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
):
    return await render_template(request, "knowledge/index.html")


@knowledge_router.post("/generate", name="knowledge.generate")
async def knowledge_generate(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    focus_area: str = Form(""),
):
    container = get_request_container()
    use_case = container.generate_knowledge_check_use_case
    page = await use_case.execute(current_user.id, focus_area)
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
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
):
    container = get_request_container()
    use_case = container.submit_knowledge_check_use_case

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
    page = await use_case.execute(questions, answers)
    page_dict = page.model_dump()
    page_dict["questions_json"] = json.dumps(
        [q.model_dump() for q in page.questions], ensure_ascii=False
    )
    return await render_template(request, "knowledge/index.html", page=page_dict)
