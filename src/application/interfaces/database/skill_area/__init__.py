"""Порт репозитория областей навыков."""

from .read import SkillAreaReadRepositoryPort


class SkillAreaRepositoryPort(SkillAreaReadRepositoryPort):
    """Комбинированный порт репозитория областей навыков.

    Справочник заполняется миграцией, поэтому порта записи здесь намеренно нет.
    """


__all__ = [
    "SkillAreaReadRepositoryPort",
    "SkillAreaRepositoryPort",
]
