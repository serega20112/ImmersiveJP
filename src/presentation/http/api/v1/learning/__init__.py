"""Модульные роуты обучения."""

from fastapi import APIRouter

from .cards import cards_router
from .export import export_router
from .speech import speech_router
from .tracks import tracks_router
from .work import work_router

learning_router = APIRouter(prefix="/learn")
learning_router.include_router(tracks_router)
learning_router.include_router(cards_router)
learning_router.include_router(speech_router)
learning_router.include_router(work_router)
learning_router.include_router(export_router)

__all__ = ["learning_router"]
