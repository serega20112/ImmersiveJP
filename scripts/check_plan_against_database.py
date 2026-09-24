"""Сверка учебного плана на живой базе: новая реализация против старой.

Страница плана не покрыта тестами, а перенос программы в таблицы прошёл только
офлайн-проверкой на SQLite. Этот скрипт сравнивает вывод на реальных данных
PostgreSQL и реального пользователя: новая версия читает программу из таблиц,
старая берёт захардкоженный _ROADMAP из HEAD git.

Использование (из корня репозитория):
    python -m scripts.check_plan_against_database [user_id]
"""

from __future__ import annotations

import asyncio
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import text

from src.application.use_cases.profile.build_learning_plan import BuildLearningPlanUseCase
from src.application.use_cases.profile.build_progress_report import BuildProgressReportUseCase
from src.infrastructures.database import database as db_module
from src.infrastructures.repositories.database import ImmersiveUnitOfWork

OLD_MODULE_SOURCE = "src/application/use_cases/profile/build_learning_plan.py"

REFERENCE_COUNT_QUERIES = {
    "course_stages": text("SELECT COUNT(*) FROM course_stages"),
    "course_modules": text("SELECT COUNT(*) FROM course_modules"),
    "course_topics": text("SELECT COUNT(*) FROM course_topics"),
    "skill_areas": text("SELECT COUNT(*) FROM skill_areas"),
}


def load_old_module() -> object:
    """Загрузить модуль плана из HEAD, где программа ещё захардкожена.

    Returns:
        Модуль со старой версией сборки плана.
    """
    root = Path(__file__).resolve().parents[1]
    source = subprocess.check_output(
        ["git", "show", f"HEAD:{OLD_MODULE_SOURCE}"],
        cwd=root,
        text=True,
        encoding="utf-8",
    )
    path = Path(tempfile.mkdtemp()) / "old_plan_live.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("old_plan_live", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["old_plan_live"] = module
    spec.loader.exec_module(module)
    return module


async def show_reference_data() -> None:
    """Напечатать содержимое справочных таблиц в PostgreSQL."""
    factory = db_module.get_session_factory()
    async with factory() as session:
        counts = {}
        for table, statement in REFERENCE_COUNT_QUERIES.items():
            result = await session.execute(statement)
            counts[table] = int(result.scalar_one())
        print("=== справочные таблицы ===")
        for table, count in counts.items():
            print(f"  {table:16} {count}")

        stage_rows = await session.execute(
            text("SELECT position, code, title FROM course_stages ORDER BY position")
        )
        print("\n=== этапы программы ===")
        for position, code, title in stage_rows:
            print(f"  {position}  {code:16} {title}")

        area_rows = await session.execute(
            text("SELECT code, title, stage_position FROM skill_areas ORDER BY code LIMIT 4")
        )
        print("\n=== области навыков (первые 4) ===")
        for code, title, stage_position in area_rows:
            print(f"  {code:24} {title}  -> этап {stage_position}")


async def build_plan(user_id: int) -> object:
    """Собрать план новой реализацией поверх боевого Unit of Work.

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Данные страницы учебного плана.
    """
    uow = ImmersiveUnitOfWork(db_module.get_session_factory())
    return await BuildLearningPlanUseCase(uow, BuildProgressReportUseCase(uow)).execute(user_id)


async def build_plan_old(user_id: int, old_module: object) -> object:
    """Собрать план старой реализацией с захардкоженным roadmap.

    Args:
        user_id: Идентификатор пользователя.
        old_module: Модуль из HEAD git.

    Returns:
        Данные страницы учебного плана.
    """
    uow = ImmersiveUnitOfWork(db_module.get_session_factory())
    use_case = old_module.BuildLearningPlanUseCase(uow, BuildProgressReportUseCase(uow))
    return await use_case.execute(user_id)


def compare(new_plan: object, old_plan: object) -> list[str]:
    """Сверить два плана поле за полем.

    Args:
        new_plan: План, собранный из таблиц.
        old_plan: План, собранный из _ROADMAP.

    Returns:
        Список расхождений; пустой при полной идентичности.
    """
    problems: list[str] = []
    for field in (
        "title",
        "subtitle",
        "horizon_title",
        "horizon_note",
        "current_stage_title",
        "current_stage_timeframe",
        "current_stage_summary",
        "recovery_note",
        "next_action",
        "parallel_note",
    ):
        new_value = getattr(new_plan, field)
        old_value = getattr(old_plan, field)
        if new_value != old_value:
            problems.append(f"{field}: {old_value!r} != {new_value!r}")

    if new_plan.content_mode != old_plan.content_mode:
        problems.append("content_mode разошёлся")
    if new_plan.pace_mode != old_plan.pace_mode:
        problems.append("pace_mode разошёлся")

    if len(new_plan.stages) != len(old_plan.stages):
        problems.append(f"число этапов {len(old_plan.stages)} != {len(new_plan.stages)}")
    for index, (new_stage, old_stage) in enumerate(
        zip(new_plan.stages, old_plan.stages, strict=False)
    ):
        if new_stage != old_stage:
            problems.append(f"этап {index} разошёлся")
            print("   old:", old_stage)
            print("   new:", new_stage)
    return problems


async def main() -> None:
    """Прогнать справочные данные и сверить план на живом пользователе."""
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    await show_reference_data()

    old_module = load_old_module()
    lookup = text("SELECT id, display_name FROM users WHERE id = :uid")
    async with db_module.get_session_factory()() as session:
        found = await session.execute(lookup, {"uid": user_id})
        row = found.first()
    if row is None:
        raise SystemExit(f"Пользователь {user_id} не найден; передай id существующего")
    print(f"\n=== план для пользователя {row[0]} ({row[1]}) ===")

    new_plan = await build_plan(user_id)
    old_plan = await build_plan_old(user_id, old_module)

    print(f"  этапов показано      : {len(new_plan.stages)}")
    print(f"  текущий этап         : {new_plan.current_stage_title}")
    print(f"  горизонт             : {new_plan.horizon_title}")
    print(f"  модулей суммарно     : {sum(len(stage.modules) for stage in new_plan.stages)}")
    print(
        f"  тем суммарно         : {sum(len(module.items) for stage in new_plan.stages for module in stage.modules)}"
    )

    problems = compare(new_plan, old_plan)
    for problem in problems[:10]:
        print("  РАСХОЖДЕНИЕ:", problem)
    print("\nRESULT:", "IDENTICAL" if not problems else f"{len(problems)} MISMATCHES")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
