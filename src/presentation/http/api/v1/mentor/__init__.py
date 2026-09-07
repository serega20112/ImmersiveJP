"""Модульные роуты ментора."""

from fastapi import APIRouter

from .page import mentor_page_router
from .send import mentor_send_router
from .voice_input import mentor_voice_router

mentor_router = APIRouter(prefix="/tutor")
mentor_router.include_router(mentor_page_router)
mentor_router.include_router(mentor_send_router)
mentor_router.include_router(mentor_voice_router)

__all__ = ["mentor_router"]
