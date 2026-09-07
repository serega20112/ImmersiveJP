"""Модульные роуты аутентификации."""

from fastapi import APIRouter

from .login import login_router
from .logout import logout_router
from .register import register_router
from .verification import verification_router

auth_router = APIRouter(prefix="/auth")
auth_router.include_router(register_router)
auth_router.include_router(login_router)
auth_router.include_router(logout_router)
auth_router.include_router(verification_router)

__all__ = ["auth_router"]
