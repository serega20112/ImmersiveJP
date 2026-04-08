from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.web.templating import flash, render_error_page

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ):
        log_event(
            logger,
            logging.WARNING,
            "http.validation_error",
            "Request validation failed",
            request_id=getattr(request.state, "request_id", None),
            path=request.url.path,
            method=request.method,
            errors=exc.errors(),
        )
        return _build_error_response(
            request=request,
            status_code=422,
            title="Нужно поправить данные",
            message="Форма заполнена некорректно. Проверь поля и попробуй еще раз.",
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ):
        if request.url.path.startswith("/static") or request.url.path == "/favicon.ico":
            return PlainTextResponse("Not found", status_code=exc.status_code)

        title = "Страница не найдена" if exc.status_code == 404 else "Ошибка запроса"
        message = (
            "Похоже, такого адреса здесь нет."
            if exc.status_code == 404
            else "Запрос не удалось обработать. Попробуй вернуться назад и повторить действие."
        )
        log_event(
            logger,
            logging.WARNING if exc.status_code < 500 else logging.ERROR,
            "http.exception",
            "HTTP exception returned to client",
            request_id=getattr(request.state, "request_id", None),
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=str(exc.detail),
        )
        return _build_error_response(
            request=request,
            status_code=exc.status_code,
            title=title,
            message=message,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ):
        logger.error(
            "Unhandled application exception",
            exc_info=exc,
            extra={
                "event": "http.unhandled_exception",
                "extra_fields": {
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": getattr(
                        getattr(request.state, "current_user", None), "id", None
                    ),
                    "error_type": type(exc).__name__,
                },
            },
        )
        return _build_error_response(
            request=request,
            status_code=500,
            title="Что-то сломалось на сервере",
            message=(
                "Запрос не удалось завершить. Ничего не потеряно, но это место лучше повторить чуть позже."
            ),
        )


def _build_error_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    message: str,
):
    if request.method != "GET":
        flash(request, message, "error")
        return RedirectResponse(url=_resolve_return_href(request), status_code=303)
    return render_error_page(
        request,
        status_code=status_code,
        title=title,
        message=message,
        return_href=_resolve_return_href(request),
    )


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
