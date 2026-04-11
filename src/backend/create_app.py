from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import time

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from src.backend.delivery.api.router import api_router
from src.backend.dependencies.container import container
from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.files import get_session_factory
from src.backend.infrastructure.observability import get_logger
from src.backend.infrastructure.web import (
    SESSION_COOKIE_NAME,
    register_exception_handlers,
)
from src.backend.infrastructure.web.middleware import (
    CsrfMiddleware,
    RequestContainerMiddleware,
    RequestLoggingMiddleware,
    RequestStateMiddleware,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PROJECT_ROOT / "src" / "frontend"
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    yield
    root_container = getattr(app.state, "root_container", None)
    if root_container is not None:
        await root_container.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title=Settings.app_name,
        debug=Settings.app_debug,
        lifespan=_lifespan,
    )
    app.state.root_container = container
    app.state.asset_version = str(int(time.time()))
    app.mount(
        "/static", StaticFiles(directory=str(FRONTEND_ROOT / "static")), name="static"
    )
    app.add_middleware(
        RequestContainerMiddleware,
        root_container=container,
        session_factory=get_session_factory(),
    )
    app.add_middleware(CsrfMiddleware)
    app.add_middleware(RequestLoggingMiddleware, logger=logger)
    app.add_middleware(RequestStateMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=Settings.session_secret,
        same_site=Settings.cookie_samesite,
        https_only=Settings.cookie_secure,
        session_cookie=SESSION_COOKIE_NAME,
    )
    app.include_router(api_router)
    register_exception_handlers(app)
    return app
