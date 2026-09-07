"""Роут списка документов пользователя."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import DocumentServiceDependency
from src.presentation.http import render_template

document_list_router = APIRouter()


@document_list_router.get("/", name="documents.page")
async def document_list(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    document_service: DocumentServiceDependency,
) -> HTMLResponse:
    """Отрисовать список документов пользователя.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        document_service: Сервис документов.

    Returns:
        Ответ с шаблоном списка документов.
    """
    documents = await document_service.list_documents(current_user.id)
    return await render_template(request, "documents/index.html", documents=documents)
