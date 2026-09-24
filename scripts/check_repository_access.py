"""Проверить, что типизированный доступ к репозиториям не врёт.

Свойства UnitOfWork собирают имена ключей в одном месте, и это место должно
совпадать с тем, что реально зарегистрировано в Unit of Work. Расхождение
не поймать ни линтером, ни тестами на подменах: тестовый FakeUnitOfWork
реализует low-level repository() и потому честно отдаёт то, что просят, а в
боевом репозитории несуществующий ключ всплывёт только в рантайме на живом
запросе.

Запуск:
    python -m scripts.check_repository_access
"""

from __future__ import annotations

import asyncio
import inspect
import re
from pathlib import Path
from typing import Any

from src.application.interfaces.database.base.unit_of_work import UnitOfWork
from src.infrastructures.repositories.database import (
    ImmersiveUnitOfWork,
    LearningCardRepository,
    ProgressRepository,
    SessionRepository,
    UserRepository,
)
from src.infrastructures.repositories.database.course import CourseRepository
from src.infrastructures.repositories.database.skill_area import SkillAreaRepository
from src.infrastructures.repositories.database.user_document import UserDocumentRepository

INTERFACE_PATH = Path("src/application/interfaces/database/base/unit_of_work.py")
SCAN_ROOTS = (Path("src"), Path("scripts"), Path("tests"))
CALL_PATTERN = re.compile(r"\w+\.repository\(\s*[\"']")
EXPECTED_TYPES: dict[str, type] = {
    "users": UserRepository,
    "learning_cards": LearningCardRepository,
    "sessions": SessionRepository,
    "progress": ProgressRepository,
    "course": CourseRepository,
    "skill_areas": SkillAreaRepository,
    "user_documents": UserDocumentRepository,
}
failures: list[str] = []


class _DummySession:
    """Сессия-заглушка: репозитории при регистрации её только сохраняют."""

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def close(self) -> None:
        pass


def report(name: str, ok: bool, detail: str = "") -> None:
    """Зарегистрировать результат проверки.

    Args:
        name: Что проверялось.
        ok: Пройдена ли проверка.
        detail: Пояснение для вывода.
    """
    status = "ok  " if ok else "FAIL"
    print(f"{status} {name} {detail}".rstrip())
    if not ok:
        failures.append(name)


def interface_properties() -> list[str]:
    """Перечислить имена типизированных свойств репозиториев в интерфейсе.

    Returns:
        Отсортированные имена свойств, отличных от низового repository.
    """
    names = [
        name
        for name, member in inspect.getmembers_static(UnitOfWork)
        if isinstance(member, property) and name != "repository"
    ]
    return sorted(names)


def check_no_locator_calls() -> None:
    """Убедиться, что в обход свойств нигде не зовут repository по имени."""
    offenders: list[str] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if path == INTERFACE_PATH:
                continue
            if CALL_PATTERN.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path))
    report(
        "прямых вызовов локатора не осталось",
        not offenders,
        f"(остались: {offenders})" if offenders else "",
    )


async def check_properties_resolve() -> None:
    """Убедиться, что каждое свойство возвращает ожидаемый репозиторий."""
    uow = ImmersiveUnitOfWork(lambda: _DummySession())

    try:
        async with uow as opened:
            for name in interface_properties():
                expected = EXPECTED_TYPES.get(name)
                if expected is None:
                    report(f"свойство {name} описано", False, "(нет ожидаемого типа в проверке)")
                    continue
                resolved: Any = getattr(opened, name)
                report(
                    f"свойство {name} ведёт на {expected.__name__}",
                    isinstance(resolved, expected),
                    f"(получено {type(resolved).__name__})"
                    if not isinstance(resolved, expected)
                    else "",
                )
    except Exception as error:
        report("единица работы открылась", False, f"({type(error).__name__}: {error})")
        return

    report("единица работы открылась", True)


def check_no_unknown_property() -> None:
    """Убедиться, что список ожидаемых типов покрывает все свойства."""
    uncovered = [name for name in interface_properties() if name not in EXPECTED_TYPES]
    report(
        "все свойства есть в проверке типов",
        not uncovered,
        f"(не покрыты: {uncovered})" if uncovered else "",
    )


def main() -> int:
    """Прогнать проверки доступа к репозиториям.

    Returns:
        Код завершения: 0 — доступ типизирован и корректен.
    """
    check_no_locator_calls()
    check_no_unknown_property()
    asyncio.run(check_properties_resolve())

    if failures:
        print(f"RESULT: {len(failures)} ПРОБЛЕМ: {', '.join(failures)}")
        return 1
    print("RESULT: REPOSITORY ACCESS IS TYPED AND RESOLVES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
