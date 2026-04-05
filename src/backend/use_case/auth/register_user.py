from __future__ import annotations

from src.backend.domain.common import normalize_email
from src.backend.domain.user import User
from src.backend.dto.auth_dto import RegistrationDTO, UserViewDTO
from src.backend.infrastructure.security import EmailVerificationStore, PasswordService
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.infrastructure.external import Mailer
from src.backend.use_case.mappers import to_user_view_dto


class EmailAlreadyExistsError(Exception):
    pass


class InvalidRegistrationDataError(Exception):
    pass


class RegisterUserUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        password_service: PasswordService,
        verification_store: EmailVerificationStore,
        mailer: Mailer,
    ):
        self._user_repository = user_repository
        self._password_service = password_service
        self._verification_store = verification_store
        self._mailer = mailer

    async def execute(self, payload: RegistrationDTO) -> UserViewDTO:
        try:
            email = normalize_email(payload.email)
        except ValueError as error:
            raise InvalidRegistrationDataError(str(error)) from error
        password = payload.password.strip()
        display_name = payload.display_name.strip()
        if len(password) < 8:
            raise InvalidRegistrationDataError(
                "Пароль должен быть не короче 8 символов"
            )
        if len(display_name) < 2 or len(display_name) > 40:
            raise InvalidRegistrationDataError(
                "Имя должно быть длиной от 2 до 40 символов"
            )
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user is not None:
            raise EmailAlreadyExistsError("Пользователь с таким email уже существует")

        user = await self._user_repository.add(
            User(
                email=email,
                password_hash=self._password_service.hash_password(password),
                display_name=display_name,
            )
        )
        code = await self._verification_store.issue_code(email)
        await self._mailer.send_verification_code(email, code)
        return to_user_view_dto(user)
