from __future__ import annotations

from src.backend.domain.common import normalize_email
from src.backend.dto.auth_dto import UserViewDTO, VerificationDTO
from src.backend.infrastructure.security import EmailVerificationStore
from src.backend.infrastructure.repositories import AbstractUserRepository
from src.backend.use_case.mappers import to_user_view_dto


class InvalidVerificationCodeError(Exception):
    pass


class VerifyEmailUseCase:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        verification_store: EmailVerificationStore,
    ):
        self._user_repository = user_repository
        self._verification_store = verification_store

    async def execute(self, payload: VerificationDTO) -> UserViewDTO:
        try:
            email = normalize_email(payload.email)
        except ValueError as error:
            raise InvalidVerificationCodeError(str(error)) from error
        code = "".join(character for character in payload.code if character.isdigit())
        user = await self._user_repository.get_by_email(email)
        if user is None:
            raise InvalidVerificationCodeError("Пользователь не найден")
        if user.is_email_verified:
            return to_user_view_dto(user)
        is_valid = await self._verification_store.verify_code(email, code)
        if not is_valid:
            raise InvalidVerificationCodeError(
                "Код подтверждения неверный или просрочен"
            )
        verified_user = await self._user_repository.mark_email_verified(int(user.id))
        return to_user_view_dto(verified_user)
