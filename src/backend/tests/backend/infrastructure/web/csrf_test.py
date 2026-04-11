from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse

import pytest
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

from src.backend.infrastructure.web.constants import (
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
)
from src.backend.infrastructure.web.csrf import ensure_csrf_token, validate_csrf
from src.backend.infrastructure.web.errors import SecurityViolationError


def _build_request(method: str, *, content_type: str = "", headers=None) -> Request:
    app = FastAPI()
    scope = {
        "type": "http",
        "app": app,
        "method": method,
        "path": "/",
        "headers": headers or [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("testserver", 80),
        "scheme": "http",
        "session": {},
    }
    if content_type:
        scope["headers"].append((b"content-type", content_type.encode("utf-8")))
    request = Request(scope)
    return request


@pytest.mark.asyncio
async def test_validate_csrf_accepts_matching_header_token():
    request = _build_request("POST", headers=[])
    token = ensure_csrf_token(request)
    request.scope["headers"].append(
        (CSRF_HEADER_NAME.lower().encode("utf-8"), token.encode("utf-8"))
    )

    await validate_csrf(request)


@pytest.mark.asyncio
async def test_validate_csrf_rejects_missing_token():
    request = _build_request("POST")
    ensure_csrf_token(request)

    with pytest.raises(SecurityViolationError) as exc:
        await validate_csrf(request)

    assert exc.value.status_code == 403


def test_validate_csrf_keeps_form_body_available_for_route_handlers():
    app = FastAPI()

    @app.middleware("http")
    async def csrf_guard(request: Request, call_next):
        await validate_csrf(request)
        return await call_next(request)

    @app.get("/")
    async def index(request: Request):
        token = ensure_csrf_token(request)
        return PlainTextResponse(token)

    @app.post("/submit")
    async def submit(
        email: str = Form(),
        password: str = Form(),
        display_name: str = Form(),
    ):
        return {"email": email, "password": password, "display_name": display_name}

    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    with TestClient(app) as client:
        token = client.get("/").text
        response = client.post(
            "/submit",
            data={
                "email": "user@example.com",
                "password": "secret123",
                "display_name": "Sergey",
                CSRF_FIELD_NAME: token,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "email": "user@example.com",
        "password": "secret123",
        "display_name": "Sergey",
    }
