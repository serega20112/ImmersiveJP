"""
Юнит-тесты use case VerifyEmailUseCase.

Проверяются: успешное подтверждение кода, повторное подтверждение,
неверный код и неизвестный пользователь.
"""

import pytest

from src.application.dto.auth import VerificationDTO
from src.application.exceptions import InvalidVerificationCodeError


class TestVerifyEmailUseCase:
    """Группа тестов юзкейса подтверждения email."""

    @pytest.fixture
    def use_case(self, fake_uow, verification_store):
        """Use case подтверждения email на подменных зависимостях."""
        from src.application.use_cases.auth.verify_email import VerifyEmailUseCase

        return VerifyEmailUseCase(fake_uow, verification_store)

    async def test_verifies_user_with_valid_code(self, use_case, fake_user_repository, user_factory, verification_store) -> None:
        """
        Тестируем: подтверждение email корректным кодом.
        Отдаём: неподтверждённый пользователь и код, выданный хранилищем.
        Ожидаем: is_email_verified=True, пользователь сохранён, DTO подтверждён.
        """
        user = user_factory.build(user_id=5)
        fake_user_repository._by_email[user.email.value] = user
        await verification_store.issue_code("user@example.com")

        result = await use_case.execute(VerificationDTO(email="user@example.com", code=verification_store.issued["user@example.com"]))

        assert result.is_email_verified is True
        assert user.is_email_verified is True
        assert user in fake_user_repository.saved

    async def test_idempotent_for_already_verified(self, use_case, fake_user_repository, user_factory) -> None:
        """
        Тестируем: повторное подтверждение уже подтверждённого email.
        Отдаём: пользователь с is_email_verified=True и произвольный код.
        Ожидаем: DTO без ошибки, save() не вызывается.
        """
        user = user_factory.build(user_id=5, is_email_verified=True)
        fake_user_repository._by_email[user.email.value] = user

        result = await use_case.execute(VerificationDTO(email="user@example.com", code="000000"))

        assert result.is_email_verified is True
        assert fake_user_repository.saved == []

    async def test_rejects_wrong_code(self, use_case, fake_user_repository, user_factory) -> None:
        """
        Тестируем: подтверждение неверным кодом.
        Отдаём: неподтверждённый пользователь и произвольный код.
        Ожидаем: выброс InvalidVerificationCodeError, флаг не меняется.
        """
        user = user_factory.build(user_id=5)
        fake_user_repository._by_email[user.email.value] = user

        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(VerificationDTO(email="user@example.com", code="999999"))

        assert user.is_email_verified is False

    async def test_rejects_unknown_user(self, use_case) -> None:
        """
        Тестируем: подтверждение для несуществующего пользователя.
        Отдаём: пустой репозиторий и любой код.
        Ожидаем: выброс InvalidVerificationCodeError.
        """
        with pytest.raises(InvalidVerificationCodeError):
            await use_case.execute(VerificationDTO(email="ghost@example.com", code="123456"))

    async def test_code_digits_extracted_from_noisy_input(self, use_case, fake_user_repository, user_factory, verification_store) -> None:
        """
        Тестируем: извлечение цифр из кода с лишними символами.
        Отдаём: код "123-456", записанный в хранилище как "123456".
        Ожидаем: подтверждение проходит успешно.
        """
        user = user_factory.build(user_id=5)
        fake_user_repository._by_email[user.email.value] = user
        await verification_store.issue_code("user@example.com")
        verification_store.issued["user@example.com"] = "123456"

        result = await use_case.execute(VerificationDTO(email="user@example.com", code="123-456"))

        assert result.is_email_verified is True
