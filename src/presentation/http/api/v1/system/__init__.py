"""Модульные системные роуты."""

from fastapi import APIRouter

from .health import health_router
from .metrics import metrics_router

system_router = APIRouter()
system_router.include_router(health_router)
system_router.include_router(metrics_router)

__all__ = ["system_router"]
