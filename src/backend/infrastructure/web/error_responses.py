from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import RedirectResponse

from src.backend.infrastructure.web.errors import ApplicationError
from src.backend.infrastructure.web.templating import flash, render_error_page


def apply_default_response_headers(request: Request, response) -> None:
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers.setdefault("X-Request-ID", request_id)


async def build_error_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    message: str,
    redirect_on_post: bool = True,
):
    if request.method != "GET" and redirect_on_post:
        flash(request, message, "error")
        response = RedirectResponse(url=_resolve_return_href(request), status_code=303)
        apply_default_response_headers(request, response)
        return response

    response = await render_error_page(
        request,
        status_code=status_code,
        title=title,
        message=message,
        return_href=_resolve_return_href(request),
    )
    response.status_code = status_code
    apply_default_response_headers(request, response)
    return response


async def build_application_error_response(
    request: Request,
    error: ApplicationError,
):
    response = await build_error_response(
        request=request,
        status_code=error.status_code,
        title=error.title,
        message=error.message,
        redirect_on_post=error.redirect_on_post,
    )
    for header_name, header_value in error.headers.items():
        response.headers.setdefault(header_name, header_value)
    return response


def _resolve_return_href(request: Request) -> str:
    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if not parsed.netloc or parsed.netloc == request.url.netloc:
            path = parsed.path or "/"
            if parsed.query:
                return f"{path}?{parsed.query}"
            return path
    return request.url.path or "/"
