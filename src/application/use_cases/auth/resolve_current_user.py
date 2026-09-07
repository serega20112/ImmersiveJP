from __future__ import annotations

import jwt

from src.application.dto.auth import UserViewDTO
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import JWTService, TokenBlocklist
from src.application.use_cases.mappers import to_user_view_dto


class ResolveCurrentUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ):
        """Initialize the resolve current user use case.

        Args:
            uow: Unit of work for database transactions.
            jwt_service: Service for JWT token operations.
            token_blocklist: Service for revoked token tracking.
        """
        self._uow = uow
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
            user_id = await self._jwt_service.decode_access_token(access_token)
        except jwt.InvalidTokenError:
            return None
        async with self._uow as uow:
            user_repository = uow.repository("user")
            user = await user_repository.get_by_id(user_id)
        return to_user_view_dto(user) if user is not None else None
