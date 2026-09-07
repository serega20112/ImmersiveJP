"""HTTP-слой презентации: роуты, middleware, рендеринг, редиректы."""

from __future__ import annotations

from .exception_handlers import register_exception_handlers
from .utils.cookies import clear_auth_cookies, set_auth_cookies
from .utils.csrf import ensure_csrf_token, validate_csrf
from .utils.flash import flash, pop_flashes
from .utils.redirects import RouteRedirectError, redirect_to_route
from .utils.rendering import get_templates, render_error_page, render_template

__all__ = [
    "RouteRedirectError",
    "clear_auth_cookies",
    "ensure_csrf_token",
    "flash",
    "get_templates",
    "pop_flashes",
    "redirect_to_route",
    "register_exception_handlers",
    "render_error_page",
    "render_template",
    "set_auth_cookies",
    "validate_csrf",
]
