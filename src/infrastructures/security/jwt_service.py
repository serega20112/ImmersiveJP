"""JWT-сервис выпуска и разбора токенов."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from src.config.settings import settings


class JWTService:
    """Выпускает и разбирает JWT-токены доступа и обновления."""

    async def create_access_token(self, user_id: int) -> str:
        """Выпустить access-токен для пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Подписанный access-токен.
        """
        return self._encode_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=settings.security.access_token_expire_minutes),
        )

    async def create_refresh_token(self, user_id: int) -> str:
        """Выпустить refresh-токен для пользователя.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Подписанный refresh-токен.
        """
        return self._encode_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=settings.security.refresh_token_expire_days),
        )

    async def decode_access_token(self, token: str) -> int:
        """Разобрать access-токен.

        Args:
            token: Значение access-токена.

        Returns:
            Идентификатор пользователя.

        Raises:
            jwt.InvalidTokenError: Токен невалиден или неверного типа.
        """
        payload = self._decode_token(token, expected_type="access")
        return int(payload["sub"])

    async def decode_refresh_token(self, token: str) -> int:
        """Разобрать refresh-токен.

        Args:
            token: Значение refresh-токена.

        Returns:
            Идентификатор пользователя.

        Raises:
            jwt.InvalidTokenError: Токен невалиден или неверного типа.
        """
        payload = self._decode_token(token, expected_type="refresh")
        return int(payload["sub"])

    async def get_token_ttl_seconds(self, token: str) -> int:
        """Вернуть остаток времени жизни токена в секундах.

        Args:
            token: Значение токена.

        Returns:
            Остаток времени жизни в секундах, не меньше нуля.
        """
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        expires_at = int(payload["exp"])
        return max(0, expires_at - int(datetime.now(tz=UTC).timestamp()))

    def _encode_token(
        self,
        user_id: int,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:
        """Подписать JWT с указанным типом и временем жизни."""
        now = datetime.now(tz=UTC)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }
        return jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

    @staticmethod
    def _decode_token(token: str, expected_type: str) -> dict:
        """Разобрать JWT и проверить тип токена."""
        payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise jwt.InvalidTokenError("Unexpected token type")
        return payload
