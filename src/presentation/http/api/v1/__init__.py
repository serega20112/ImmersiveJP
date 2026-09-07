"""Реестр роутов API v1."""

from fastapi import APIRouter

from src.presentation.http.api.v1.auth import auth_router
from src.presentation.http.api.v1.dashboard import dashboard_router
from src.presentation.http.api.v1.documents import document_router
from src.presentation.http.api.v1.index import index_router
from src.presentation.http.api.v1.knowledge import knowledge_router
from src.presentation.http.api.v1.learning import learning_router
from src.presentation.http.api.v1.mentor import mentor_router
from src.presentation.http.api.v1.onboarding import onboarding_router
from src.presentation.http.api.v1.profile import profile_router
from src.presentation.http.api.v1.system import system_router

v1_router = APIRouter()
v1_router.include_router(system_router)
v1_router.include_router(index_router)
v1_router.include_router(knowledge_router)
v1_router.include_router(auth_router)
v1_router.include_router(onboarding_router)
v1_router.include_router(document_router)
v1_router.include_router(mentor_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(learning_router)
v1_router.include_router(profile_router)

__all__ = ["v1_router"]
