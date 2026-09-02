from __future__ import annotations


class RouteRedirectError(Exception):
    def __init__(self, location: str):
        super().__init__(location)
        self.location = location
