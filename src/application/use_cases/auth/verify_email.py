from __future__ import annotations

from src.application.dto.auth import UserViewDTO, VerificationDTO
from src.application.exceptions import InvalidVerificationCodeError
from src.application.interfaces import UnitOfWork
from src.application.interfaces.clients import EmailVerificationStore
from src.application.use_cases.mappers import to_user_view_dto
from src.domain.exceptions import InvalidEmailError
from src.domain.value_objects import Email


class VerifyEmailUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        verification_store: EmailVerificationStore,
    ):
        """Initialize the verify email use case.

        Args:
            uow: Unit of work for database transactions.
            verification_store: Store for email verification codes.
        """
        self._uow = uow
        self._verification_store = verification_store

    async def execute(self, payload: VerificationDTO) -> UserViewDTO:
        """Verify a user's email with a verification code.

        Args:
            payload: The verification data (email and code).

        Returns:
            The verified user view data.

        Raises:
            InvalidVerificationCodeError: If the code is invalid or expired.
        """
        try:
            email = Email(payload.email)
        except InvalidEmailError as error:
            raise InvalidVerificationCodeError(str(error)) from error
        code = "".join(character for character in payload.code if character.isdigit())
        async with self._uow as uow:
            user_repository = uow.repository("user")
            user = await user_repository.get_by_email(email.value)
            if user is None:
                raise InvalidVerificationCodeError("Пользователь не найден")
            if user.is_email_verified:
                return to_user_view_dto(user)
            is_valid = await self._verification_store.verify_code(email.value, code)
            if not is_valid:
                raise InvalidVerificationCodeError("Код подтверждения неверный или просрочен")
            user.verify_email()
            verified_user = await user_repository.save(user)
            return to_user_view_dto(verified_user)
