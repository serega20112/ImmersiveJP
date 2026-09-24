"""
Юнит-тесты DTO аутентификации.

Проверяются: обязательность полей, неизменяемость (frozen),
значения по умолчанию и вложенность моделей регистрации/входа/токенов.
"""

import pytest
from pydantic import ValidationError

from src.application.dto.auth import (
    AuthResultDTO,
    AuthTokensDTO,
    LoginDTO,
    RegistrationDTO,
    UserViewDTO,
    VerificationDTO,
)


class TestRegistrationDTO:
    """Группа тестов DTO регистрации нового пользователя."""

    def test_builds_with_all_required_fields(self) -> None:
        """
        Тестируем: создание DTO регистрации со всеми полями.
        Отдаём: email, пароль и отображаемое имя.
        Ожидаем: поля сохранены без изменений.
        """
        dto = RegistrationDTO(email="a@a.com", password="secret", display_name="Ая")

        assert (dto.email, dto.password, dto.display_name) == ("a@a.com", "secret", "Ая")

    @pytest.mark.parametrize(
        "missing_field",
        ["email", "password", "display_name"],
        ids=["email", "password", "display-name"],
    )
    def test_raises_when_required_field_missing(self, missing_field: str) -> None:
        """
        Тестируем: валидацию обязательных полей DTO регистрации.
        Отдаём: словарь без одного из обязательных ключей.
        Ожидаем: ValidationError при построении модели.
        """
        payload = {"email": "a@a.com", "password": "secret", "display_name": "Ая"}
        payload.pop(missing_field)

        with pytest.raises(ValidationError):
            RegistrationDTO(**payload)

    def test_is_frozen(self) -> None:
        """
        Тестируем: неизменяемость DTO регистрации.
        Отдаём: созданный DTO и попытку изменить поле.
        Ожидаем: ValidationError на присваивании.
        """
        dto = RegistrationDTO(email="a@a.com", password="secret", display_name="Ая")

        with pytest.raises(ValidationError):
            dto.email = "b@b.com"  # type: ignore[misc]


class TestVerificationAndLoginDTO:
    """Группа тестов DTO подтверждения почты и входа."""

    def test_verification_dto_keeps_code(self) -> None:
        """
        Тестируем: DTO подтверждения почты.
        Отдаём: email и код подтверждения.
        Ожидаем: оба значения сохранены.
        """
        dto = VerificationDTO(email="a@a.com", code="123456")

        assert dto.code == "123456"

    def test_login_dto_keeps_credentials(self) -> None:
        """
        Тестируем: DTO учётных данных входа.
        Отдаём: email и пароль.
        Ожидаем: оба значения сохранены.
        """
        dto = LoginDTO(email="a@a.com", password="secret")

        assert (dto.email, dto.password) == ("a@a.com", "secret")


class TestUserViewDTO:
    """Группа тестов публичного представления пользователя."""

    def test_optional_profile_fields_default_to_none(self) -> None:
        """
        Тестируем: значения по умолчанию необязательных полей профиля.
        Отдаём: только обязательные поля пользователя.
        Ожидаем: goal/level/timeline равны None, interests — пустой список.
        """
        dto = UserViewDTO(
            id=1,
            email="a@a.com",
            display_name="Ая",
            is_email_verified=False,
            onboarding_completed=False,
        )

        assert dto.learning_goal is None
        assert dto.language_level is None
        assert dto.study_timeline is None
        assert dto.interests == []

    def test_interests_list_is_not_shared_between_instances(self) -> None:
        """
        Тестируем: изоляцию default_factory для списка интересов.
        Отдаём: два DTO без явных интересов, мутацию списка первого.
        Ожидаем: список второго экземпляра остаётся пустым.
        """
        first = UserViewDTO(
            id=1, email="a@a.com", display_name="Ая", is_email_verified=True, onboarding_completed=True
        )
        second = UserViewDTO(
            id=2, email="b@b.com", display_name="Би", is_email_verified=True, onboarding_completed=True
        )

        first.interests.append("аниме")

        assert second.interests == []


class TestAuthResultDTO:
    """Группа тестов агрегата результата аутентификации."""

    def test_nests_user_and_tokens(self) -> None:
        """
        Тестируем: вложенность пользователя и пары токенов.
        Отдаём: UserViewDTO и AuthTokensDTO.
        Ожидаем: обе части доступны через поля результата.
        """
        user = UserViewDTO(
            id=1, email="a@a.com", display_name="Ая", is_email_verified=True, onboarding_completed=True
        )
        tokens = AuthTokensDTO(access_token="acc", refresh_token="ref")

        result = AuthResultDTO(user=user, tokens=tokens)

        assert result.user.display_name == "Ая"
        assert result.tokens.refresh_token == "ref"
