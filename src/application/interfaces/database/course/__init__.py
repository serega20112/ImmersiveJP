"""Порты репозитория учебной программы."""

from .read import CourseReadRepositoryPort


class CourseRepositoryPort(CourseReadRepositoryPort):
    """Комбинированный порт репозитория учебной программы.

    Программа — справочные данные, они заполняются миграцией, поэтому порта
    записи здесь намеренно нет.
    """


__all__ = [
    "CourseReadRepositoryPort",
    "CourseRepositoryPort",
]
