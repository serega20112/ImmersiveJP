from __future__ import annotations

from fastapi import APIRouter, Request

from src.backend.infrastructure.web import render_template

index_router = APIRouter()


@index_router.get("/", name="index.landing")
async def landing_page(request: Request):
    """Render the landing page.

    Args:
        request: The incoming request.

    Returns:
        The rendered landing template.
    """
    return await render_template(request, "landing.html")
