from __future__ import annotations

import jwt

from src.backend.dto.auth_dto import UserViewDTO
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.infrastructure.security import JWTService, TokenBlocklist
from src.backend.use_case.mappers import to_user_view_dto


class ResolveCurrentUserUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ):
        """Initialize the resolve current user use case.

        Args:
            user_repository: Repository for user data.
            jwt_service: Service for JWT token operations.
            token_blocklist: Service for revoked token tracking.
        """
        self._user_repository = user_repository
        self._jwt_service = jwt_service
        self._token_blocklist = token_blocklist

    async def execute(self, access_token: str | None) -> UserViewDTO | None:
        """Resolve the current user from an access token.

        Args:
            access_token: The access token to decode and validate.

        Returns:
            The user view data, or None if token is invalid or revoked.
        """
        if not access_token:
            return None
        if await self._token_blocklist.is_revoked(access_token):
            return None
        try:
            user_id = self._jwt_service.decode_access_token(access_token)
        except jwt.InvalidTokenError:
            return None
        user = await self._user_repository.get_by_id(user_id)
        return to_user_view_dto(user) if user is not None else None
