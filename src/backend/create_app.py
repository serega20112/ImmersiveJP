from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.backend.delivery.api.v1.auth_route import auth_router
from src.backend.delivery.api.v1.dashboard_route import dashboard_router
from src.backend.delivery.api.v1.index_route import index_router
from src.backend.delivery.api.v1.learning_route import learning_router
from src.backend.delivery.api.v1.onboarding_route import onboarding_router
from src.backend.delivery.api.v1.profile_route import profile_router
from src.backend.dependencies.container import container
from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.files import get_session_factory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(title=Settings.app_name, debug=Settings.app_debug)
    app.state.root_container = container
    app.state.asset_version = str(int(time.time()))
    app.add_middleware(
        SessionMiddleware,
        secret_key=Settings.session_secret,
        same_site=Settings.cookie_samesite,
        https_only=Settings.cookie_secure,
        session_cookie="immersjp_session",
    )
    app.mount(
        "/static", StaticFiles(directory=str(FRONTEND_ROOT / "static")), name="static"
    )

    @app.middleware("http")
    async def request_scope(request: Request, call_next):
        request.state.db_session = None
        request.state.container = app.state.root_container.scope(
            session_factory=get_session_factory(),
            request_state=request.state,
        )
        request.state.current_user = None
        access_token = request.cookies.get("access_token")
        request.state.current_user = (
            await request.state.container.auth_service.resolve_current_user(
                access_token
            )
        )
        try:
            response = await call_next(request)
        finally:
            await request.state.container.aclose()
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await app.state.root_container.shutdown()

    app.include_router(index_router)
    app.include_router(auth_router)
    app.include_router(onboarding_router)
    app.include_router(dashboard_router)
    app.include_router(learning_router)
    app.include_router(profile_router)
    return app
