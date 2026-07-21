from __future__ import annotations

from fastapi import Request
from fastapi.responses import RedirectResponse


def redirect_to_route(request: Request, route_name: str) -> RedirectResponse:
    """Redirect to a named route.

    Args:
        request: The incoming request.
        route_name: The name of the route to redirect to.

    Returns:
        A redirect response to the route.
    """
    return RedirectResponse(url=request.app.url_path_for(route_name), status_code=303)


def track_href(track: str) -> str:
    """Get the href for a track by its key.

    Args:
        track: The track key (language, culture, history).

    Returns:
        The track URL path.
    """
    return {
        "language": "/learn/language",
        "culture": "/learn/culture",
        "history": "/learn/history",
    }[track]


def resolve_return_to(return_to: str | None, fallback: str) -> str:
    """Resolve a return URL, falling back to a default.

    Args:
        return_to: The return URL, or None.
        fallback: The fallback URL.

    Returns:
        The resolved URL string.
    """
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return fallback
