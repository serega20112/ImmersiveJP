"""
Юнит-тесты use case RegisterUserUseCase.

Проверяется бизнес-логика регистрации: успешное создание пользователя
с отправкой кода подтверждения, обработка дублирующегося email и
некорректных данных, а также корректность вызовов зависимостей
(репозиторий пользователей, сервис хеширования, хранилище кодов, mailer).
"""

import pytest

from src.application.dto.auth import RegistrationDTO
from src.application.exceptions import EmailAlreadyExistsError, InvalidRegistrationDataError
from tests.fixtures.factories.user_factory import UserFactory


def _payload(email: str = "a@a.com", password: str = "12345678", display_name: str = "Сергей") -> RegistrationDTO:
    """Собрать DTO регистрации с значениями по умолчанию.

    Args:
        email: Адрес электронной почты.
        password: Пароль пользователя.
        display_name: Отображаемое имя.

    Returns:
        RegistrationDTO для передачи в use case.
    """
    return RegistrationDTO(email=email, password=password, display_name=display_name)


class TestRegisterUserUseCase:
    """Группа тестов юзкейса регистрации нового пользователя."""

    async def test_creates_user_and_sends_verification_code(self, register_use_case, fake_user_repository, password_service, verification_store, mailer) -> None:
        """
        Тестируем: успешное создание пользователя при уникальном email.
        Отдаём: данные нового пользователя; репозиторий не содержит такого email.
        Ожидаем: пользователь добавлен в репозиторий; код подтверждения выдан и отправлен;
                 результат содержит нормализованный email и не подтверждённый флаг.
        """
        result = await register_use_case.execute(_payload(email="User@Example.COM"))

        assert fake_user_repository.added, "пользователь должен быть сохранён"
        added = fake_user_repository.added[0]
        assert added.email.value == "user@example.com"
        assert added.password_hash.value == "hashed:12345678"
        assert result.email == "user@example.com"
        assert result.display_name == "Сергей"
        assert result.is_email_verified is False
        assert verification_store.issued == {"user@example.com": verification_store.issued.get("user@example.com")}
        assert verification_store.issued["user@example.com"]
        assert mailer.sent == [("user@example.com", verification_store.issued["user@example.com"])]
        assert password_service.hashed == ["12345678"]

    async def test_raises_when_email_already_registered(self, register_use_case, fake_uow, fake_user_repository, mailer) -> None:
        """
        Тестируем: попытку регистрации с уже занятым email.
        Отдаём: репозиторий, в котором по этому email найден существующий пользователь.
        Ожидаем: выброс EmailAlreadyExistsError, новый пользователь не сохраняется,
                 письмо с кодом не отправляется.
        """
        existing = UserFactory(user_id=1).build()
        fake_user_repository._by_email[existing.email.value] = existing
        register_use_case._uow = fake_uow

        with pytest.raises(EmailAlreadyExistsError):
            await register_use_case.execute(_payload(email=existing.email.value))

        assert fake_user_repository.added == []
        assert mailer.sent == []

    @pytest.mark.parametrize(
        "invalid_email",
        ["plainaddress", "@no-local-part.com", "no-at-sign.com", "spaces in@email.com"],
        ids=["no-at", "no-local-part", "no-domain-dot", "contains-spaces"],
    )
    async def test_raises_on_invalid_email(self, register_use_case, fake_user_repository, invalid_email: str) -> None:
        """
        Тестируем: валидацию формата email до обращения к репозиторию.
        Отдаём: заведомо невалидные email-строки.
        Ожидаем: выброс InvalidRegistrationDataError, сохранения не происходит.
        """
        with pytest.raises(InvalidRegistrationDataError):
            await register_use_case.execute(_payload(email=invalid_email))

        assert fake_user_repository.added == []

    @pytest.mark.parametrize("short_password", ["", "1234567", "   123456 "], ids=["empty", "seven-chars", "whitespace-trimmed"])
    async def test_raises_on_short_password(self, register_use_case, fake_user_repository, short_password: str) -> None:
        """
        Тестируем: проверку минимальной длины пароля (после trim).
        Отдаём: пароли короче 8 символов, в том числе с пробелами по краям.
        Ожидаем: выброс InvalidRegistrationDataError, сохранения не происходит.
        """
        with pytest.raises(InvalidRegistrationDataError):
            await register_use_case.execute(_payload(password=short_password))

        assert fake_user_repository.added == []

    async def test_raises_on_invalid_display_name(self, register_use_case, fake_user_repository) -> None:
        """
        Тестируем: валидацию отображаемого имени.
        Отдаём: имя из одних пробелов.
        Ожидаем: выброс InvalidRegistrationDataError, сохранения не происходит.
        """
        with pytest.raises(InvalidRegistrationDataError):
            await register_use_case.execute(_payload(display_name="   "))

        assert fake_user_repository.added == []
