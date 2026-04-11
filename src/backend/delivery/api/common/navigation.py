from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse


def redirect_to_route(request: Request, route_name: str) -> RedirectResponse:
    return RedirectResponse(url=request.app.url_path_for(route_name), status_code=303)


def track_href(track: str) -> str:
    return {
        "language": "/learn/language",
        "culture": "/learn/culture",
        "history": "/learn/history",
    }[track]


def resolve_return_to(return_to: str | None, fallback: str) -> str:
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return fallback
