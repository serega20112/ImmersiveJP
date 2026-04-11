from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.web.constants import CSRF_FIELD_NAME
from src.backend.infrastructure.web.csrf import ensure_csrf_token

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TEMPLATES_ROOT = PROJECT_ROOT / "src" / "frontend" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_ROOT))


def flash(request: Request, message: str, category: str = "info") -> None:
    queue = list(request.session.get("flash_messages", []))
    queue.append({"message": message, "category": category})
    request.session["flash_messages"] = queue


def pop_flashes(request: Request) -> list[dict[str, str]]:
    messages = list(request.session.get("flash_messages", []))
    request.session["flash_messages"] = []
    return messages


def render_template(request: Request, template_name: str, **context):
    template_context = {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
        "flash_messages": pop_flashes(request),
        "asset_version": getattr(request.app.state, "asset_version", "dev"),
        "text_input_limit": Settings.text_input_limit,
        "csrf_token": ensure_csrf_token(request),
        "csrf_field_name": CSRF_FIELD_NAME,
        **context,
    }
    return templates.TemplateResponse(template_name, template_context)


def render_error_page(
    request: Request,
    *,
    status_code: int,
    title: str,
    message: str,
    return_href: str,
    return_label: str = "Вернуться",
):
    response = render_template(
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
