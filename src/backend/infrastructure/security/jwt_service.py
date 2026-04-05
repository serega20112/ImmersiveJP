from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from src.backend.dependencies.settings import Settings


class JWTService:
    def create_access_token(self, user_id: int) -> str:
        return self._encode_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=Settings.access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: int) -> str:
        return self._encode_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=Settings.refresh_token_expire_days),
        )

    def decode_access_token(self, token: str) -> int:
        payload = self._decode_token(token, expected_type="access")
        return int(payload["sub"])

    def decode_refresh_token(self, token: str) -> int:
        payload = self._decode_token(token, expected_type="refresh")
        return int(payload["sub"])

    def get_token_ttl_seconds(self, token: str) -> int:
        payload = jwt.decode(
            token,
            Settings.secret_key,
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
        now = datetime.now(tz=UTC)
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }
        return jwt.encode(payload, Settings.secret_key, algorithm="HS256")

    @staticmethod
    def _decode_token(token: str, expected_type: str) -> dict:
        payload = jwt.decode(token, Settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != expected_type:
            raise jwt.InvalidTokenError("Unexpected token type")
        return payload
