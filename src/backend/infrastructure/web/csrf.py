from __future__ import annotations

from secrets import compare_digest, token_urlsafe

from fastapi import Request

from src.backend.infrastructure.web.constants import (
    CSRF_FIELD_NAME,
    CSRF_HEADER_NAME,
    CSRF_SESSION_KEY,
)
from src.backend.infrastructure.web.errors import SecurityViolationError

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def ensure_csrf_token(request: Request) -> str:
    token = str(request.session.get(CSRF_SESSION_KEY) or "").strip()
    if token:
        return token
    token = token_urlsafe(32)
    request.session[CSRF_SESSION_KEY] = token
    return token


async def validate_csrf(request: Request) -> None:
    if request.method.upper() in _SAFE_METHODS:
        ensure_csrf_token(request)
        return

    session_token = ensure_csrf_token(request)
    submitted_token = str(request.headers.get(CSRF_HEADER_NAME) or "").strip()
    if not submitted_token:
        content_type = str(request.headers.get("content-type") or "").lower()
        if (
            "application/x-www-form-urlencoded" in content_type
            or "multipart/form-data" in content_type
        ):
            # Buffer the body before parsing the form so BaseHTTPMiddleware
            # can still replay it to downstream FastAPI form handlers.
            await request.body()
            form = await request.form()
            submitted_token = str(form.get(CSRF_FIELD_NAME) or "").strip()

    if not submitted_token or not compare_digest(session_token, submitted_token):
        raise SecurityViolationError()
