from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

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
        **context,
    }
    return templates.TemplateResponse(template_name, template_context)
