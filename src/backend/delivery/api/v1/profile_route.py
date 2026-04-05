from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request

from src.backend.delivery.api.v1.helpers import get_current_user
from src.backend.delivery.api.v1.helpers import get_profile_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.infrastructure.web import render_template

profile_router = APIRouter()


@profile_router.get("/profile", name="profile.page")
async def profile_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.login_page")
    report = await get_profile_service(request).build_progress_report(current_user.id)
    advice = await get_profile_service(request).generate_ai_advice(
        current_user.id, report
    )
    return render_template(request, "profile/index.html", report=report, advice=advice)
