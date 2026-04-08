from __future__ import annotations

from fastapi import APIRouter
from fastapi import Form
from fastapi import Request

from src.backend.delivery.api.v1.helpers import get_current_user
from src.backend.delivery.api.v1.helpers import get_profile_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.infrastructure.web import flash
from src.backend.infrastructure.web import render_template
from src.backend.use_case.profile import InvalidMentorMessageError

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


@profile_router.get("/plan", name="profile.plan_page")
async def plan_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.login_page")
    page = await get_profile_service(request).build_learning_plan(current_user.id)
    return render_template(request, "profile/plan.html", page=page)


@profile_router.get("/mentor", name="profile.mentor_page")
async def mentor_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.login_page")
    page = await get_profile_service(request).get_mentor_page(current_user.id)
    return render_template(request, "profile/mentor.html", page=page)


@profile_router.post("/mentor", name="profile.mentor_send")
async def mentor_send(
    request: Request,
    message: str = Form(),
):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, "auth.login_page")
    try:
        page = await get_profile_service(request).send_mentor_message(
            current_user.id,
            message,
        )
        return render_template(request, "profile/mentor.html", page=page)
    except InvalidMentorMessageError as error:
        flash(request, str(error), "error")
        return redirect_to_route(request, "profile.mentor_page")
