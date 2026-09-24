"""
Юнит-тесты use case ResolveCurrentUserUseCase.

Проверяется разрешение текущего пользователя из access-токена: успешный
возврат DTO, а также все ветки "пользователь не определён" — отсутствие
токена, отозванный токен, невалидная подпись и отсутствие пользователя в БД.
"""

import jwt

from src.application.use_cases.auth.resolve_current_user import ResolveCurrentUserUseCase
from tests.fixtures.factories.user_factory import UserFactory


class _FakeJwtService:
    """Подмена JWTService: выдаёт id пользователя или имитирует невалидный токен."""

    def __init__(self, user_id: int | None = 5, invalid: bool = False) -> None:
        """Инициализировать поведение разбора токена.

        Args:
            user_id: Идентификатор, возвращаемый при успешном разборе.
            invalid: Если True, разбор выбрасывает jwt.InvalidTokenError.
        """
        self.user_id = user_id
        self.invalid = invalid

    async def decode_access_token(self, token: str) -> int:  # noqa: ARG002
        """Разобрать access-токен.

        Args:
            token: Проверяемый токен (в подмене не используется).

        Returns:
            Идентификатор пользователя.

        Raises:
            jwt.InvalidTokenError: Если задан режим невалидного токена.
        """
        if self.invalid:
            raise jwt.InvalidTokenError("bad token")
        return int(self.user_id or 0)


class _FakeTokenBlocklist:
    """Подмена TokenBlocklist с настраиваемым набором отозванных токенов."""

    def __init__(self, revoked: set[str] | None = None) -> None:
        """Инициализировать блок-лист.

        Args:
            revoked: Множество отозванных токенов.
        """
        self._revoked = revoked or set()

    async def is_revoked(self, token: str) -> bool:
        """Сообщить, отозван ли токен.

        Args:
            token: Проверяемый токен.

        Returns:
            True, если токен присутствует в блок-листе.
        """
        return token in self._revoked


class TestResolveCurrentUserUseCase:
    """Группа тестов юзкейса разрешения текущего пользователя по токену."""

    async def test_returns_user_view_for_valid_token(self, fake_uow, fake_user_repository) -> None:
        """
        Тестируем: успешное разрешение пользователя по валидному токену.
        Отдаём: токен, соответствующий ему пользователь с id=5 в репозитории,
                блок-лист пуст.
        Ожидаем: UserViewDTO с id=5 и email сохранённого пользователя.
        """
        user = UserFactory().build(user_id=5)
        fake_user_repository._by_id[5] = user
        use_case = ResolveCurrentUserUseCase(
            uow=fake_uow,
            jwt_service=_FakeJwtService(user_id=5),
            token_blocklist=_FakeTokenBlocklist(),
        )

        result = await use_case.execute("valid-token")

        assert result is not None
        assert result.id == 5
        assert result.email == user.email.value

    async def test_returns_none_when_token_absent(self, fake_uow) -> None:
        """
        Тестируем: разрешение при отсутствии токена.
        Отдаём: access_token=None.
        Ожидаем: None без обращения к зависимостям.
        """
        use_case = ResolveCurrentUserUseCase(
            uow=fake_uow,
            jwt_service=_FakeJwtService(),
            token_blocklist=_FakeTokenBlocklist(),
        )

        assert await use_case.execute(None) is None

    async def test_returns_none_when_token_revoked(self, fake_uow) -> None:
        """
        Тестируем: обработку отозванного токена.
        Отдаём: токен, присутствующий в блок-листе.
        Ожидаем: None, разбор токена не выполняется.
        """
        use_case = ResolveCurrentUserUseCase(
            uow=fake_uow,
            jwt_service=_FakeJwtService(),
            token_blocklist=_FakeTokenBlocklist(revoked={"revoked-token"}),
        )

        assert await use_case.execute("revoked-token") is None

    async def test_returns_none_when_token_invalid(self, fake_uow) -> None:
        """
        Тестируем: обработку токена с невалидной подписью.
        Отдаём: JWT-сервис, выбрасывающий jwt.InvalidTokenError.
        Ожидаем: None вместо проброса исключения.
        """
        use_case = ResolveCurrentUserUseCase(
            uow=fake_uow,
            jwt_service=_FakeJwtService(invalid=True),
            token_blocklist=_FakeTokenBlocklist(),
        )

        assert await use_case.execute("tampered-token") is None

    async def test_returns_none_when_user_not_found(self, fake_uow) -> None:
        """
        Тестируем: ситуацию, когда токен валиден, но пользователя нет в БД.
        Отдаём: пустой репозиторий и токен, разбирающийся в id=99.
        Ожидаем: None.
        """
        use_case = ResolveCurrentUserUseCase(
            uow=fake_uow,
            jwt_service=_FakeJwtService(user_id=99),
            token_blocklist=_FakeTokenBlocklist(),
        )

        assert await use_case.execute("valid-token") is None
