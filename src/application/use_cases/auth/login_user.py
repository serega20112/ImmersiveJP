from __future__ import annotations

from src.application.dto.auth import AuthResultDTO, AuthTokensDTO, LoginDTO
from src.application.exceptions import EmailNotVerifiedError, InvalidCredentialsError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import JWTService, PasswordService
from src.application.use_cases.mappers import to_user_view_dto
from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects import Email


class LoginUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_service: PasswordService,
        jwt_service: JWTService,
    ):
        """Initialize the login user use case.

        Args:
            uow: Unit of work for database transactions.
            password_service: Service for password verification.
            jwt_service: Service for JWT token creation.
        """
        self._uow = uow
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def execute(self, payload: LoginDTO) -> AuthResultDTO:
        """Authenticate a user and generate auth tokens.

        Args:
            payload: The login credentials.

        Returns:
            The authentication result with tokens.

        Raises:
            InvalidCredentialsError: If email or password is invalid.
            EmailNotVerifiedError: If email has not been verified.
        """
        try:
            email = Email(payload.email)
        except InvalidEmailError as error:
            raise InvalidCredentialsError(str(error)) from error
        async with self._uow as uow:
            user_repository = uow.users
            user = await user_repository.get_by_email(email.value)
        if user is None or user.id is None or not await self._password_service.verify_password(
            payload.password,
            user.password_hash.value,
        ):
            raise InvalidCredentialsError("Неверный email или пароль")
        if not user.is_email_verified:
            raise EmailNotVerifiedError("Сначала подтверди почту")
        return AuthResultDTO(
            user=to_user_view_dto(user),
            tokens=AuthTokensDTO(
                access_token=await self._jwt_service.create_access_token(int(user.id)),
                refresh_token=await self._jwt_service.create_refresh_token(int(user.id)),
            ),
        )
