from __future__ import annotations

from src.backend.dto.profile_dto import DashboardDTO
from src.backend.use_case.dashboard import GetDashboardUseCase


class DashboardService:
    def __init__(self, get_dashboard_use_case: GetDashboardUseCase):
        self._get_dashboard_use_case = get_dashboard_use_case

    async def get_dashboard(self, user_id: int) -> DashboardDTO:
        return await self._get_dashboard_use_case.execute(user_id)
