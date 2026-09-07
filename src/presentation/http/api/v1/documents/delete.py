"""Роут удаления документа."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import DocumentServiceDependency
from src.presentation.http import flash, redirect_to_route

document_delete_router = APIRouter()


@document_delete_router.post("/{doc_id}/delete", name="documents.delete")
async def document_delete(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    document_service: DocumentServiceDependency,
    doc_id: int,
) -> RedirectResponse:
    """Обработать удаление документа.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        document_service: Сервис документов.
        doc_id: Идентификатор документа.

    Returns:
        Редирект на список документов.
    """
    is_deleted = await document_service.delete_document(current_user.id, doc_id)
    if is_deleted:
        flash(request, "Материал удалён.", "success")
    else:
        flash(request, "Материал не найден.", "error")
    return redirect_to_route(request, "documents.page")
