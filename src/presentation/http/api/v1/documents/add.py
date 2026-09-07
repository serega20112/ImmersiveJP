"""Роут добавления документа."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from src.application.dto.auth import UserViewDTO
from src.infrastructures.di_containers.auth_dependencies import require_onboarded_user
from src.infrastructures.di_containers.service_dependencies import DocumentServiceDependency
from src.presentation.http import flash, redirect_to_route
from src.presentation.http.schemas import DocumentAddForm

document_add_router = APIRouter()


@document_add_router.post("/add", name="documents.add")
async def document_add(
    request: Request,
    current_user: Annotated[UserViewDTO, Depends(require_onboarded_user)],
    document_service: DocumentServiceDependency,
    form: Annotated[DocumentAddForm, Depends()],
) -> RedirectResponse:
    """Обработать добавление нового документа.

    Args:
        request: Входящий запрос.
        current_user: Авторизованный пользователь с онбордингом.
        document_service: Сервис документов.
        form: Данные формы документа.

    Returns:
        Редирект на список документов.
    """
    await document_service.add_document(current_user.id, form.title, form.content)
    flash(request, "Материал сохранён.", "success")
    return redirect_to_route(request, "documents.page")
