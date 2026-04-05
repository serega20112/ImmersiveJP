from __future__ import annotations

from src.backend.domain.common import normalize_email
from src.backend.dto.auth_dto import AuthResultDTO, AuthTokensDTO, LoginDTO
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.infrastructure.security import JWTService, PasswordService
from src.backend.use_case.mappers import to_user_view_dto


class InvalidCredentialsError(Exception):
    pass


class EmailNotVerifiedError(Exception):
    pass


class LoginUserUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        password_service: PasswordService,
        jwt_service: JWTService,
    ):
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def execute(self, payload: LoginDTO) -> AuthResultDTO:
        try:
            email = normalize_email(payload.email)
        except ValueError as error:
            raise InvalidCredentialsError(str(error)) from error
        user = await self._user_repository.get_by_email(email)
        if user is None or not self._password_service.verify_password(
            payload.password,
            user.password_hash,
        ):
            raise InvalidCredentialsError("Неверный email или пароль")
        if not user.is_email_verified:
            raise EmailNotVerifiedError("Сначала подтверди почту")
        return AuthResultDTO(
            user=to_user_view_dto(user),
            tokens=AuthTokensDTO(
                access_token=self._jwt_service.create_access_token(int(user.id)),
                refresh_token=self._jwt_service.create_refresh_token(int(user.id)),
            ),
        )
