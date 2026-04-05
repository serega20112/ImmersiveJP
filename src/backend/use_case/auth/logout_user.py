from __future__ import annotations

from src.backend.infrastructure.security import JWTService, TokenBlocklist


class LogoutUserUseCase:
    def __init__(self, jwt_service: JWTService, token_blocklist: TokenBlocklist):
        self._jwt_service = jwt_service
        self._token_blocklist = token_blocklist

    async def execute(
        self,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        for token in (access_token, refresh_token):
            if not token:
                continue
            ttl_seconds = self._jwt_service.get_token_ttl_seconds(token)
            await self._token_blocklist.revoke(token, ttl_seconds)
