"""Сервис хеширования и проверки паролей."""

from __future__ import annotations

from passlib.context import CryptContext


class PasswordService:
    """Хеширует пароли алгоритмом pbkdf2_sha256 и проверяет их."""

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    async def hash_password(self, password: str) -> str:
        """Хешировать пароль.

        Args:
            password: Пароль в открытом виде.

        Returns:
            Хеш пароля.
        """
        return self._context.hash(password)

    async def verify_password(self, password: str, password_hash: str) -> bool:
        """Проверить пароль против хеша.

        Args:
            password: Пароль в открытом виде.
            password_hash: Сохранённый хеш пароля.

        Returns:
            True, если пароль совпадает с хешем.
        """
        return self._context.verify(password, password_hash)
