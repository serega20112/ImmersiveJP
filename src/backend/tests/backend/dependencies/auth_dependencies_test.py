from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi import Request

from src.backend.dependencies.auth_dependencies import (
    require_authenticated_user,
    require_onboarded_user,
    require_registered_user,
)
from src.backend.infrastructure.web import RouteRedirectError


def _build_request(current_user=None) -> Request:
    app = FastAPI()

    @app.get("/auth/login", name="auth.login_page")
    async def _login():
        return {}

    @app.get("/auth/register", name="auth.register_page")
    async def _register():
        return {}

    @app.get("/onboarding", name="onboarding.page")
    async def _onboarding():
        return {}

    scope = {
        "type": "http",
        "app": app,
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 5000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    request = Request(scope)
    request.state.current_user = current_user
    return request


@pytest.mark.asyncio
async def test_require_registered_user_redirects_to_register():
    request = _build_request()

    with pytest.raises(RouteRedirectError) as exc:
        await require_registered_user(request)

    assert exc.value.location == "/auth/register"


@pytest.mark.asyncio
async def test_require_authenticated_user_returns_current_user():
    current_user = SimpleNamespace(id=7, onboarding_completed=False)
    request = _build_request(current_user=current_user)

    resolved = await require_authenticated_user(request)

    assert resolved is current_user


@pytest.mark.asyncio
async def test_require_onboarded_user_redirects_when_profile_not_finished():
    current_user = SimpleNamespace(id=11, onboarding_completed=False)
    request = _build_request(current_user=current_user)

    with pytest.raises(RouteRedirectError) as exc:
        await require_onboarded_user(request)

    assert exc.value.location == "/onboarding"
