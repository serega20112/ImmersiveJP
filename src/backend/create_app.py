from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.backend.delivery.api.router import api_router
from src.backend.dependencies.container import container
from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.files import get_session_factory
from src.backend.infrastructure.observability import (
    configure_logging,
    get_logger,
    log_event,
)
from src.backend.infrastructure.web import register_exception_handlers

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield
    await app.state.root_container.shutdown()


def create_app() -> FastAPI:
    configure_logging(Settings.log_level)
    app = FastAPI(
        title=Settings.app_name,
        debug=Settings.app_debug,
        lifespan=_lifespan,
    )
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
        started_at = time.perf_counter()
        request_id = uuid4().hex
        request.state.request_id = request_id
        request.state.db_session = None
        request.state.container = app.state.root_container.scope(
            session_factory=get_session_factory(),
            request_state=request.state,
        )
        request.state.current_user = None
        response = None
        try:
            access_token = request.cookies.get("access_token")
            request.state.current_user = (
                await request.state.container.auth_service.resolve_current_user(
                    access_token
                )
            )
            response = await call_next(request)
        except Exception:
            if not request.url.path.startswith("/static"):
                log_event(
                    logger,
                    logging.ERROR,
                    "http.request_failed",
                    "Request failed",
                    request_id=request_id,
                    path=request.url.path,
                    method=request.method,
                    user_id=getattr(request.state.current_user, "id", None),
                    duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
                )
            raise
        finally:
            await request.state.container.aclose()
        if not request.url.path.startswith("/static"):
            log_event(
                logger,
                logging.INFO,
                "http.request_completed",
                "Request completed",
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                user_id=getattr(request.state.current_user, "id", None),
                status_code=response.status_code,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("X-Request-ID", request_id)
        return response

    app.include_router(api_router)
    register_exception_handlers(app)
    return app
