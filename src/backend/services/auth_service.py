from __future__ import annotations

from src.backend.dto.auth_dto import (
    AuthResultDTO,
    LoginDTO,
    RegistrationDTO,
    UserViewDTO,
    VerificationDTO,
)
from src.backend.use_case.auth import (
    LoginUserUseCase,
    LogoutUserUseCase,
    RegisterUserUseCase,
    ResolveCurrentUserUseCase,
    VerifyEmailUseCase,
)


class AuthService:
    def __init__(
        self,
        register_user_use_case: RegisterUserUseCase,
        verify_email_use_case: VerifyEmailUseCase,
        login_user_use_case: LoginUserUseCase,
        logout_user_use_case: LogoutUserUseCase,
        resolve_current_user_use_case: ResolveCurrentUserUseCase,
    ):
        """Initialize the auth service.

        Args:
            register_user_use_case: Use case for user registration.
            verify_email_use_case: Use case for email verification.
            login_user_use_case: Use case for user login.
            logout_user_use_case: Use case for user logout.
            resolve_current_user_use_case: Use case for resolving the current user.
        """
        self._register_user_use_case = register_user_use_case
        self._verify_email_use_case = verify_email_use_case
        self._login_user_use_case = login_user_use_case
        self._logout_user_use_case = logout_user_use_case
        self._resolve_current_user_use_case = resolve_current_user_use_case

    async def register(self, payload: RegistrationDTO) -> UserViewDTO:
        """Register a new user.

        Args:
            payload: The registration data.

        Returns:
            The created user view data.
        """
        return await self._register_user_use_case.execute(payload)

    async def verify_email(self, payload: VerificationDTO) -> UserViewDTO:
        """Verify a user's email address.

        Args:
            payload: The verification data (email and code).

        Returns:
            The updated user view data.
        """
        return await self._verify_email_use_case.execute(payload)

    async def login(self, payload: LoginDTO) -> AuthResultDTO:
        """Authenticate a user and return tokens.

        Args:
            payload: The login credentials.

        Returns:
            The authentication result with tokens.
        """
        return await self._login_user_use_case.execute(payload)

    async def logout(self, access_token: str | None, refresh_token: str | None) -> None:
        """Log out a user by revoking tokens.

        Args:
            access_token: The access token to revoke.
            refresh_token: The refresh token to revoke.
        """
        await self._logout_user_use_case.execute(access_token, refresh_token)

    async def resolve_current_user(self, access_token: str | None) -> UserViewDTO | None:
        """Resolve the current user from an access token.

        Args:
            access_token: The access token to decode.

        Returns:
            The user view data, or None if invalid.
        """
        return await self._resolve_current_user_use_case.execute(access_token)
