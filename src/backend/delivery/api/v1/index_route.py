from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request

from src.backend.infrastructure.web import render_template

index_router = APIRouter()


@index_router.get('/', name='index.landing')
async def landing_page(request: Request):
    return render_template(request, 'landing.html')