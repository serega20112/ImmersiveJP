from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request

from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.dependencies.auth_dependencies import require_onboarded_user
from src.backend.dependencies.service_dependencies import UserDocumentRepositoryDependency
from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.web import flash, render_template

document_router = APIRouter(prefix="/documents")


@document_router.get("", name="documents.page")
async def document_list(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    doc_repo: UserDocumentRepositoryDependency,
):
    """Render the document list page.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        doc_repo: The document repository dependency.

    Returns:
        The rendered documents template.
    """
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
    """Handle adding a new document.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        doc_repo: The document repository dependency.
        title: The document title.
        content: The document content.

    Returns:
        A redirect response.
    """
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
    """Handle deleting a document.

    Args:
        request: The incoming request.
        current_user: The authenticated and onboarded user.
        doc_repo: The document repository dependency.
        doc_id: ID of the document to delete.

    Returns:
        A redirect response.
    """
    doc = await doc_repo.get(doc_id)
    if doc is not None and doc.user_id == current_user.id:
        await doc_repo.delete(doc_id)
        flash(request, "Материал удалён.", "success")
    else:
        flash(request, "Материал не найден.", "error")
    return redirect_to_route(request, "documents.page")
