from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.backend.infrastructure.observability import get_logger, log_event
from src.backend.infrastructure.web.error_responses import (
    apply_default_response_headers,
    build_application_error_response,
    build_error_response,
)
from src.backend.infrastructure.web.errors import ApplicationError
from src.backend.infrastructure.web.redirects import RouteRedirectError

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RouteRedirectError)
    async def handle_route_redirect(request: Request, exc: RouteRedirectError):
        response = RedirectResponse(url=exc.location, status_code=303)
        apply_default_response_headers(request, response)
        return response

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        return await build_application_error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
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
        response = await build_error_response(
            request=request,
            status_code=422,
            title="Нужно поправить данные",
            message="Форма заполнена некорректно. Проверь поля и попробуй еще раз.",
        )
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/static") or request.url.path == "/favicon.ico":
            response = PlainTextResponse("Not found", status_code=exc.status_code)
            apply_default_response_headers(request, response)
            return response

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
        response = await build_error_response(
            request=request,
            status_code=exc.status_code,
            title=title,
            message=message,
        )
        return response

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
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
        response = await build_error_response(
            request=request,
            status_code=500,
            title="Что-то сломалось на сервере",
            message=(
                "Запрос не удалось завершить. Ничего не потеряно, но это место лучше повторить чуть позже."
            ),
        )
        return response
