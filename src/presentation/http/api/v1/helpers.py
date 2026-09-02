from src.infrastructures.di_containers.current_user import get_current_user, resolve_current_user
from src.presentation.http.api.common.cookies import clear_auth_cookies, set_auth_cookies
from src.presentation.http.api.common.navigation import (
    redirect_to_route,
    resolve_return_to,
    track_href,
)
from src.presentation.http.api.common.services import (
    get_auth_service,
    get_dashboard_service,
    get_learning_service,
    get_onboarding_service,
    get_profile_service,
)
