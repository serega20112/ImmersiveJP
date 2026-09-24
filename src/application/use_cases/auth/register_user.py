from __future__ import annotations

from src.application.dto.auth import RegistrationDTO, UserViewDTO
from src.application.exceptions import EmailAlreadyExistsError, InvalidRegistrationDataError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import EmailVerificationStore, Mailer, PasswordService
from src.application.use_cases.mappers import to_user_view_dto
from src.domain.aggregates.user import User
from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects import DisplayName, Email, PasswordHash


class RegisterUserUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        password_service: PasswordService,
        verification_store: EmailVerificationStore,
        mailer: Mailer,
    ):
        """Initialize the register user use case.

        Args:
            uow: Unit of work for database transactions.
            password_service: Service for password hashing.
            verification_store: Store for email verification codes.
            mailer: Service for sending emails.
        """
        self._uow = uow
        self._password_service = password_service
        self._verification_store = verification_store
        self._mailer = mailer

    async def execute(self, payload: RegistrationDTO) -> UserViewDTO:
        """Register a new user and send a verification email.

        Args:
            payload: The registration data.

        Returns:
            The created user view data.

        Raises:
            InvalidRegistrationDataError: If registration data is invalid.
            EmailAlreadyExistsError: If the email is already taken.
        """
        try:
            email = Email(payload.email)
        except InvalidEmailError as error:
            raise InvalidRegistrationDataError(str(error)) from error
        password = payload.password.strip()
        display_name_raw = payload.display_name.strip()
        if len(password) < 8:
            raise InvalidRegistrationDataError("Пароль должен быть не короче 8 символов")
        try:
            display_name = DisplayName(display_name_raw)
        except Exception as error:
            raise InvalidRegistrationDataError(str(error)) from error
        async with self._uow as uow:
            user_repository = uow.users
            existing_user = await user_repository.get_by_email(email.value)
            if existing_user is not None:
                raise EmailAlreadyExistsError("Пользователь с таким email уже существует")

            user = await user_repository.add(
                User.create(
                    email=email,
                    password_hash=PasswordHash(await self._password_service.hash_password(password)),
                    display_name=display_name,
                )
            )
        code = await self._verification_store.issue_code(email.value)
        await self._mailer.send_verification_code(email.value, code)
        return to_user_view_dto(user)
