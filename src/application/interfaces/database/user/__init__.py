"""Порты репозитория пользователей."""

from .read import UserReadRepositoryPort
from .write import UserWriteRepositoryPort


class UserRepositoryPort(UserReadRepositoryPort, UserWriteRepositoryPort):
    """Комбинированный порт репозитория пользователей."""


__all__ = [
    "UserReadRepositoryPort",
    "UserRepositoryPort",
    "UserWriteRepositoryPort",
]
