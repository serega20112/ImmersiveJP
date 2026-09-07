"""Рендеринг HTML-шаблонов с базовым контекстом."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.config.settings import settings
from src.presentation.http.utils.csrf import ensure_csrf_token
from src.presentation.http.utils.flash import pop_flashes


def get_templates(request: Request) -> Jinja2Templates:
    """Получить настроенный на этапе сборки приложения шаблонизатор.

    Args:
        request: Входящий запрос.

    Returns:
        Экземпляр Jinja2Templates из состояния приложения.
    """
    return request.app.state.templates


async def render_template(
    request: Request,
    template_name: str,
    **context,
) -> HTMLResponse:
    """Отрендерить шаблон с базовым контекстом.

    Args:
        request: Входящий запрос.
        template_name: Имя шаблона.
        **context: Дополнительный контекст шаблона.

    Returns:
        Ответ с отрендеренным шаблоном.
    """
    from src.infrastructures.di_containers.current_user import (
        get_current_user,
        resolve_current_user,
    )

    current_user = get_current_user(request)
    if current_user is None:
        current_user = await resolve_current_user(request)
    template_context = {
        "request": request,
        "current_user": current_user,
        "flash_messages": pop_flashes(request),
        "asset_version": getattr(request.app.state, "asset_version", "dev"),
        "text_input_limit": settings.app.text_input_limit,
        "csrf_token": ensure_csrf_token(request),
        "csrf_field_name": settings.security.csrf_field_name,
        **context,
    }
    return request.app.state.templates.TemplateResponse(
        request, template_name, template_context
    )


async def render_error_page(
    request: Request,
    *,
    status_code: int,
    title: str,
    message: str,
    return_href: str,
    return_label: str = "Вернуться",
) -> HTMLResponse:
    """Отрендерить страницу ошибки с заданным статусом.

    Args:
        request: Входящий запрос.
        status_code: HTTP-статус ошибки.
        title: Заголовок страницы ошибки.
        message: Текст сообщения об ошибке.
        return_href: Адрес возврата.
        return_label: Подпись кнопки возврата.

    Returns:
        Ответ со страницей ошибки.
    """
    response = await render_template(
        request,
        "errors/error.html",
        page={
            "status_code": status_code,
            "title": title,
            "message": message,
            "return_href": return_href,
            "return_label": return_label,
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    response.status_code = status_code
    return response
