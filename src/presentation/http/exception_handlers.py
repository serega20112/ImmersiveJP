"""Глобальные обработчики исключений HTTP-слоя на примитивах Starlette.

Презентационный слой не определяет собственных ошибок: он перехватывает
исключения прикладного и доменного слоёв (``src.application.exceptions``)
и отображает их на HTTP: статус выводится из кода ошибки, для GET отдаётся
страница ошибки, для POST — PRG-редирект назад с flash-сообщением.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.exceptions import ApplicationError, ErrorCode
from src.presentation.http.utils.flash import flash
from src.presentation.http.utils.redirects import RouteRedirectError
from src.presentation.http.utils.rendering import render_error_page
from src.utils.logging import get_logger, log_event

logger = get_logger(__name__)

ERROR_STATUS_CODES: dict[ErrorCode, int] = {
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.ALREADY_EXISTS: 409,
    ErrorCode.VALIDATION: 422,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.UNAUTHORIZED: 403,
    ErrorCode.INTERNAL: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
}

ERROR_TITLES: dict[ErrorCode, str] = {
    ErrorCode.NOT_FOUND: "Страница не найдена",
    ErrorCode.ALREADY_EXISTS: "Конфликт данных",
    ErrorCode.VALIDATION: "Некорректные данные",
    ErrorCode.UNAUTHENTICATED: "Требуется вход",
    ErrorCode.UNAUTHORIZED: "Доступ запрещён",
    ErrorCode.INTERNAL: "Ошибка сервера",
    ErrorCode.SERVICE_UNAVAILABLE: "Сервис временно недоступен",
    ErrorCode.CONFLICT: "Конфликт данных",
    ErrorCode.RATE_LIMITED: "Слишком много запросов",
}


def error_status_code(error: ApplicationError) -> int:
    """Определить HTTP-статус по коду ошибки приложения.

    Args:
        error: Ошибка приложения.

    Returns:
        HTTP-статус, соответствующий коду ошибки.
    """
    return ERROR_STATUS_CODES.get(error.code, 500)


def apply_default_response_headers(request: Request, response) -> None:
    """Добавить к ответу безопасные заголовки по умолчанию.

    Args:
        request: Входящий запрос.
        response: Ответ, к которому добавляются заголовки.
    """
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers.setdefault("X-Request-ID", request_id)


async def application_error_response(request: Request, error: ApplicationError):
    """Собрать ответ на ошибку приложения средствами Starlette.

    Для POST-запросов выполняется PRG-редирект назад с flash-сообщением,
    для остальных — страница ошибки. Заголовки rate limit выводятся
    из деталей ошибки.

    Args:
        request: Входящий запрос.
        error: Ошибка прикладного/доменного слоя.

    Returns:
        Ответ с ошибкой и безопасными заголовками.
    """
    response = await _error_response(
        request,
        status_code=error_status_code(error),
        title=ERROR_TITLES.get(error.code, "Ошибка сервера"),
        message=error.message,
    )
    if error.code is ErrorCode.RATE_LIMITED:
        retry_after = error.details.get("retry_after_seconds")
        if retry_after is not None:
            response.headers.setdefault("Retry-After", str(retry_after))
        limit = error.details.get("limit")
        if limit is not None:
            response.headers.setdefault("X-RateLimit-Limit", str(limit))
        remaining = error.details.get("remaining")
        if remaining is not None:
            response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
    return response


async def _error_response(
    request: Request,
    *,
    status_code: int,
    title: str,
    message: str,
):
    """Собрать ответ на ошибку: POST — редирект с flash, иначе страница.

    Args:
        request: Входящий запрос.
        status_code: HTTP-статус ошибки.
        title: Заголовок страницы ошибки.
        message: Текст сообщения об ошибке.

    Returns:
        Ответ с ошибкой и безопасными заголовками.
    """
    if request.method != "GET":
        flash(request, message, "error")
        response = RedirectResponse(url=_return_href(request), status_code=303)
        apply_default_response_headers(request, response)
        return response
    response = await render_error_page(
        request,
        status_code=status_code,
        title=title,
        message=message,
        return_href=_return_href(request),
    )
    apply_default_response_headers(request, response)
    return response


def _return_href(request: Request) -> str:
    """Определить безопасный адрес возврата по заголовку referer.

    Args:
        request: Входящий запрос.

    Returns:
        Относительный адрес возврата на тот же домен.
    """
    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if not parsed.netloc or parsed.netloc == request.url.netloc:
            path = parsed.path or "/"
            if parsed.query:
                return f"{path}?{parsed.query}"
            return path
    return request.url.path or "/"


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать обработчики исключений приложения.

    Args:
        app: Приложение FastAPI.
    """

    @app.exception_handler(RouteRedirectError)
    async def handle_route_redirect(request: Request, exc: RouteRedirectError):
        """Выполнить редирект по исключению-сигналу.

        Args:
            request: Входящий запрос.
            exc: Исключение редиректа.

        Returns:
            Редирект-ответ.
        """
        response = RedirectResponse(url=exc.location, status_code=303)
        apply_default_response_headers(request, response)
        return response

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        """Преобразовать ошибку приложения в HTTP-ответ.

        Args:
            request: Входящий запрос.
            exc: Ошибка прикладного/доменного слоя.

        Returns:
            Ответ с ошибкой.
        """
        return await application_error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        """Обработать ошибку валидации формы.

        Args:
            request: Входящий запрос.
            exc: Ошибка валидации запроса.

        Returns:
            Ответ с ошибкой валидации.
        """
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
        return await _error_response(
            request,
            status_code=422,
            title="Нужно поправить данные",
            message="Форма заполнена некорректно. Проверьте поля и попробуйте ещё раз.",
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        """Обработать HTTP-исключение Starlette.

        Args:
            request: Входящий запрос.
            exc: HTTP-исключение.

        Returns:
            Ответ с ошибкой.
        """
        if request.url.path.startswith("/static") or request.url.path == "/favicon.ico":
            response = PlainTextResponse("Not found", status_code=exc.status_code)
            apply_default_response_headers(request, response)
            return response

        title = "Страница не найдена" if exc.status_code == 404 else "Ошибка запроса"
        message = (
            "Похоже, такого адреса здесь нет."
            if exc.status_code == 404
            else "Запрос не удалось обработать. Попробуйте вернуться назад и повторить действие."
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
        return await _error_response(
            request,
            status_code=exc.status_code,
            title=title,
            message=message,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        """Обработать непредвиденное исключение сервера.

        Args:
            request: Входящий запрос.
            exc: Непредвиденное исключение.

        Returns:
            Ответ с ошибкой 500.
        """
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unhandled application exception",
            exc_info=exc,
            extra={
                "event": "http.unhandled_exception",
                "extra_fields": {
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": getattr(
                        getattr(request.state, "current_user", None), "id", None
                    ),
                    "error_type": type(exc).__name__,
                },
            },
        )
        return await _error_response(
            request,
            status_code=500,
            title="Что-то сломалось на сервере",
            message=(
                f"Произошла непредвиденная ошибка. Пожалуйста, обратитесь в поддержку, "
                f"указав этот код: {request_id}"
            ),
        )
