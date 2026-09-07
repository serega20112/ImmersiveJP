"""Модульные роуты онбординга."""

from fastapi import APIRouter

from .complete import onboarding_complete_router
from .page import onboarding_page_router

onboarding_router = APIRouter()
onboarding_router.include_router(onboarding_page_router)
onboarding_router.include_router(onboarding_complete_router)

__all__ = ["onboarding_router"]
