"""Модульные роуты профиля."""

from fastapi import APIRouter

from .mentor import profile_mentor_router
from .plan import plan_page_router
from .profile import profile_page_router

profile_router = APIRouter()
profile_router.include_router(profile_page_router)
profile_router.include_router(plan_page_router)
profile_router.include_router(profile_mentor_router)

__all__ = ["profile_router"]
