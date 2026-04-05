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
        self._register_user_use_case = register_user_use_case
        self._verify_email_use_case = verify_email_use_case
        self._login_user_use_case = login_user_use_case
        self._logout_user_use_case = logout_user_use_case
        self._resolve_current_user_use_case = resolve_current_user_use_case

    async def register(self, payload: RegistrationDTO) -> UserViewDTO:
        return await self._register_user_use_case.execute(payload)

    async def verify_email(self, payload: VerificationDTO) -> UserViewDTO:
        return await self._verify_email_use_case.execute(payload)

    async def login(self, payload: LoginDTO) -> AuthResultDTO:
        return await self._login_user_use_case.execute(payload)

    async def logout(self, access_token: str | None, refresh_token: str | None) -> None:
        await self._logout_user_use_case.execute(access_token, refresh_token)

    async def resolve_current_user(
        self, access_token: str | None
    ) -> UserViewDTO | None:
        return await self._resolve_current_user_use_case.execute(access_token)
