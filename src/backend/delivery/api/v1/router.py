from fastapi import APIRouter

from src.backend.delivery.api.v1.auth_route import auth_router
from src.backend.delivery.api.v1.dashboard_route import dashboard_router
from src.backend.delivery.api.v1.index_route import index_router
from src.backend.delivery.api.v1.learning_route import learning_router
from src.backend.delivery.api.v1.onboarding_route import onboarding_router
from src.backend.delivery.api.v1.profile_route import profile_router

v1_router = APIRouter()
v1_router.include_router(index_router)
v1_router.include_router(auth_router)
v1_router.include_router(onboarding_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(learning_router)
v1_router.include_router(profile_router)
