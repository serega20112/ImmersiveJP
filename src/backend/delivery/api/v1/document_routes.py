from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request

from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.service_dependencies import UserDocumentRepositoryDependency
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template

document_router = APIRouter(prefix="/documents")


@document_router.get("", name="documents.page")
async def document_list(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    doc_repo: UserDocumentRepositoryDependency,
):
    documents = await doc_repo.get_by_user(current_user.id)
    return await render_template(request, "documents/index.html", documents=documents)


@document_router.post("/add", name="documents.add")
async def document_add(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    doc_repo: UserDocumentRepositoryDependency,
    title: str = Form(),
    content: str = Form(),
):
    await doc_repo.create(current_user.id, title, content)
    flash(request, "Материал сохранён.", "success")
    return redirect_to_route(request, "documents.page")


@document_router.post("/{doc_id}/delete", name="documents.delete")
async def document_delete(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    doc_repo: UserDocumentRepositoryDependency,
    doc_id: int,
):
    doc = await doc_repo.get(doc_id)
    if doc is not None and doc.user_id == current_user.id:
        await doc_repo.delete(doc_id)
        flash(request, "Материал удалён.", "success")
    else:
        flash(request, "Материал не найден.", "error")
    return redirect_to_route(request, "documents.page")
