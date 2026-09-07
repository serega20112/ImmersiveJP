"""Модульные роуты документов пользователя."""

from fastapi import APIRouter

from .add import document_add_router
from .delete import document_delete_router
from .list import document_list_router

document_router = APIRouter(prefix="/documents")
document_router.include_router(document_list_router)
document_router.include_router(document_add_router)
document_router.include_router(document_delete_router)

__all__ = ["document_router"]
