from __future__ import annotations

from src.backend.infrastructure.security import JWTService, TokenBlocklist


class LogoutUserUseCase:
    def __init__(self, jwt_service: JWTService, token_blocklist: TokenBlocklist):
        """Initialize the logout user use case.

        Args:
            jwt_service: Service for JWT token operations.
            token_blocklist: Service for revoked token tracking.
        """
        self._jwt_service = jwt_service
        self._token_blocklist = token_blocklist

    async def execute(
        self,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        """Revoke user tokens to log them out.

        Args:
            access_token: The access token to revoke.
            refresh_token: The refresh token to revoke.
        """
        for token in (access_token, refresh_token):
            if not token:
                continue
            ttl_seconds = self._jwt_service.get_token_ttl_seconds(token)
            await self._token_blocklist.revoke(token, ttl_seconds)
