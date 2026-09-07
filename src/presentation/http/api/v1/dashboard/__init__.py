"""Модульные роуты дашборда."""

from fastapi import APIRouter

from .page import dashboard_page_router

dashboard_router = APIRouter()
dashboard_router.include_router(dashboard_page_router)

__all__ = ["dashboard_router"]
