"""Роут главной страницы."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.presentation.http import render_template

landing_router = APIRouter()


@landing_router.get("/", name="index.landing")
async def landing_page(request: Request) -> HTMLResponse:
    """Отрисовать лендинг.

    Args:
        request: Входящий запрос.

    Returns:
        Ответ с шаблоном лендинга.
    """
    return await render_template(request, "landing.html")
