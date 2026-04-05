from __future__ import annotations

from fastapi import APIRouter
from fastapi import Request

from src.backend.delivery.api.v1.helpers import get_current_user
from src.backend.delivery.api.v1.helpers import get_dashboard_service
from src.backend.delivery.api.v1.helpers import redirect_to_route
from src.backend.infrastructure.web import render_template

dashboard_router = APIRouter()


@dashboard_router.get('/dashboard', name='dashboard.dashboard_page')
async def dashboard_page(request: Request):
    current_user = get_current_user(request)
    if current_user is None:
        return redirect_to_route(request, 'auth.login_page')
    if not current_user.onboarding_completed:
        return redirect_to_route(request, 'onboarding.page')
    dashboard = await get_dashboard_service(request).get_dashboard(current_user.id)
    return render_template(request, 'dashboard/index.html', dashboard=dashboard)