from __future__ import annotations

import pytest
from fastapi import Request

from src.backend.dependencies.current_user import resolve_current_user
from src.backend.dependencies.request_scope import _UNRESOLVED_CURRENT_USER


@pytest.mark.asyncio
async def test_resolve_current_user_returns_none_without_request_container():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 5000),
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )
    request.state.current_user = _UNRESOLVED_CURRENT_USER

    resolved = await resolve_current_user(request)

    assert resolved is None
    assert request.state.current_user is None
