from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.application.interfaces import UnitOfWork
from src.application.services import (
    AuthService,
    DashboardService,
    DocumentService,
    KnowledgeService,
    LearningService,
    OnboardingService,
    ProfileService,
)
from src.infrastructures.di_containers.request_scope import get_request_container
from src.infrastructures.external import STTClient


def get_auth_service() -> AuthService:
    """Получить сервис аутентификации из request-скоупа."""
    return get_request_container().auth_service


def get_onboarding_service() -> OnboardingService:
    """Получить сервис онбординга из request-скоупа."""
    return get_request_container().onboarding_service


def get_dashboard_service() -> DashboardService:
    """Получить сервис дашборда из request-скоупа."""
    return get_request_container().dashboard_service


def get_learning_service() -> LearningService:
    """Получить сервис обучения из request-скоупа."""
    return get_request_container().learning_service


def get_profile_service() -> ProfileService:
    """Получить сервис профиля из request-скоупа."""
    return get_request_container().profile_service


def get_knowledge_service() -> KnowledgeService:
    """Получить сервис проверки знаний из request-скоупа."""
    return get_request_container().knowledge_service


def get_document_service() -> DocumentService:
    """Получить сервис документов из request-скоупа."""
    return get_request_container().document_service


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]
OnboardingServiceDependency = Annotated[OnboardingService, Depends(get_onboarding_service)]
DashboardServiceDependency = Annotated[DashboardService, Depends(get_dashboard_service)]
LearningServiceDependency = Annotated[LearningService, Depends(get_learning_service)]
ProfileServiceDependency = Annotated[ProfileService, Depends(get_profile_service)]
KnowledgeServiceDependency = Annotated[KnowledgeService, Depends(get_knowledge_service)]
DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]


def get_stt_client() -> STTClient:
    """Получить STT-клиент из корневого контейнера."""
    return get_request_container().root.stt_client


STTClientDependency = Annotated[STTClient, Depends(get_stt_client)]


def get_database_uow() -> UnitOfWork:
    """Получить Unit of Work из request-скоупа."""
    return get_request_container().uow


DatabaseUnitOfWorkDependency = Annotated[UnitOfWork, Depends(get_database_uow)]
