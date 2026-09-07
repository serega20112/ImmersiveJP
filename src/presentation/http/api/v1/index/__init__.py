"""Модульные роуты главной страницы."""

from fastapi import APIRouter

from .landing import landing_router

index_router = APIRouter()
index_router.include_router(landing_router)

__all__ = ["index_router"]
