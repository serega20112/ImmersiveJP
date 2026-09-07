"""Модульные роуты проверки знаний."""

from fastapi import APIRouter

from .generate import knowledge_generate_router
from .page import knowledge_page_router
from .submit import knowledge_submit_router

knowledge_router = APIRouter(prefix="/check")
knowledge_router.include_router(knowledge_page_router)
knowledge_router.include_router(knowledge_generate_router)
knowledge_router.include_router(knowledge_submit_router)

__all__ = ["knowledge_router"]
