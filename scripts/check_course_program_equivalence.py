"""Сверка учебного плана до и после переноса roadmap в базу.

Скрипт загружает справочные данные миграции в SQLite, читает их через новый
CourseRepository и сравнивает результат с тем, что отдавал старый код с
захардкоженным _ROADMAP. Нужен, потому что страницу плана не покрывает ни один
тест, а перенос 118 строк данных вручную легко роняет опечатку.

Использование (из корня репозитория, чтобы корень попал в sys.path):
    python -m scripts.check_course_program_equivalence
"""

from __future__ import annotations

import asyncio
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.application.use_cases.profile import build_learning_plan as new_module
from src.domain.entities.course import CourseModule, CourseStage, CourseTopic
from src.infrastructures.database.database import Base
from src.infrastructures.database.models import (
    CourseModuleModel,
    CourseStageModel,
    CourseTopicModel,
)
from src.infrastructures.repositories.database.course import CourseRepository

ROOT = Path(__file__).resolve().parents[1]


def load_old_module() -> object:
    """Загрузить модуль плана из HEAD git, где roadmap ещё захардкожен.

    Returns:
        Модуль со старым `_ROADMAP` и старыми функциями сборки.
    """
    source = subprocess.check_output(
        ["git", "show", "HEAD:src/application/use_cases/profile/build_learning_plan.py"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    path = Path(tempfile.mkdtemp()) / "old_plan.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("old_plan", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["old_plan"] = module
    spec.loader.exec_module(module)
    return module


def load_migration_rows() -> tuple[list[dict], list[dict], list[dict]]:
    """Вытащить seed-строки из файла ревизии Alembic.

    Returns:
        Списки строк этапов, модулей и тем, которыми заполняется база.
    """
    revisions = sorted((ROOT / "build" / "alembic" / "versions").glob("*course_program.py"))
    if not revisions:
        raise SystemExit("Ревизия с учебной программой не найдена")
    spec = importlib.util.spec_from_file_location("course_rev", revisions[0])
    module = importlib.util.module_from_spec(spec)
    sys.modules["course_rev"] = module
    spec.loader.exec_module(module)
    return module.STAGE_ROWS, module.MODULE_ROWS, module.TOPIC_ROWS


async def seed_and_read(
    stage_rows: list[dict], module_rows: list[dict], topic_rows: list[dict]
) -> list[CourseStage]:
    """Записать справочные данные в SQLite и прочитать их репозиторием.

    Args:
        stage_rows: Строки таблицы этапов.
        module_rows: Строки таблицы модулей.
        topic_rows: Строки таблицы тем.

    Returns:
        Этапы программы так, как их видит приложение.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    stages_by_id = {row["id"]: row for row in stage_rows}
    async with factory() as session:
        for row in stage_rows:
            session.add(CourseStageModel(**row))
        await session.flush()
        for row in module_rows:
            session.add(CourseModuleModel(**row))
        await session.flush()
        for row in topic_rows:
            session.add(CourseTopicModel(**row))
        await session.commit()

        repository = CourseRepository(session)
        stages = await repository.list_stages()
        single = await repository.get_stage("basic-grammar")
    await engine.dispose()

    if single is None or single.title != stages_by_id[2]["title"]:
        raise SystemExit("get_stage вернул не тот этап")
    return stages


def check_rows_match_old_roadmap(
    old: object, stage_rows: list[dict], module_rows: list[dict], topic_rows: list[dict]
) -> list[str]:
    """Сверить строки миграции с исходным захардкоженным roadmap.

    Args:
        old: Старый модуль с `_ROADMAP`.
        stage_rows: Строки этапов из ревизии.
        module_rows: Строки модулей из ревизии.
        topic_rows: Строки тем из ревизии.

    Returns:
        Список расхождений; пустой, если данные совпали.
    """
    problems: list[str] = []
    roadmap = old._ROADMAP

    if len(roadmap) != len(stage_rows):
        problems.append(f"число этапов {len(roadmap)} != {len(stage_rows)}")

    for expected, row in zip(roadmap, stage_rows, strict=True):
        if expected["index"] != row["position"]:
            problems.append(f"позиция этапа {expected['index']} != {row['position']}")
        for field in ("title", "timeframe", "summary"):
            if expected[field] != row[field]:
                problems.append(f"этап {row['position']}, поле {field} разошлось")

    modules_by_stage: dict[int, list[dict]] = {}
    for row in module_rows:
        modules_by_stage.setdefault(row["stage_id"], []).append(row)

    topics_by_module: dict[int, list[dict]] = {}
    for row in topic_rows:
        topics_by_module.setdefault(row["module_id"], []).append(row)

    for expected, stage_row in zip(roadmap, stage_rows, strict=True):
        stage_modules = modules_by_stage.get(stage_row["id"], [])
        if len(stage_modules) != len(expected["modules"]):
            problems.append(f"этап {stage_row['position']}: число модулей разошлось")
            continue
        for (title, items), module_row in zip(expected["modules"], stage_modules, strict=True):
            if title != module_row["title"]:
                problems.append(f"модуль {module_row['id']}: название разошлось")
            module_topics = topics_by_module.get(module_row["id"], [])
            if [topic["title"] for topic in module_topics] != list(items):
                problems.append(f"модуль {module_row['id']}: темы разошлись: {items}")
    return problems


async def compare(old: object, stages: list[CourseStage]) -> list[str]:
    """Собрать план старым и новым кодом на одинаковых входах и сравнить.

    Args:
        old: Старый модуль с `_ROADMAP`.
        stages: Этапы, прочитанные из базы.

    Returns:
        Список расхождений; пустой, если вывод идентичен.
    """
    problems: list[str] = []
    grid = range(0, 8)
    for current in grid:
        for progress in grid:
            for weak in (None, *grid):
                for horizon in grid:
                    before = old._build_stage_dtos(
                        current_stage_index=current,
                        progress_stage_index=progress,
                        weak_stage_index=weak,
                        visible_horizon_index=horizon,
                    )
                    after = new_module._build_stage_dtos(
                        program=stages,
                        current_stage_index=current,
                        progress_stage_index=progress,
                        weak_stage_index=weak,
                        visible_horizon_index=horizon,
                    )
                    if before != after:
                        problems.append(
                            f"этапы расходятся: current={current} progress={progress} "
                            f"weak={weak} horizon={horizon}"
                        )

    from src.domain.value_objects.user import StudyTimeline

    for timeline in StudyTimeline:
        for horizon in grid:
            old_stage = old._ROADMAP[horizon]
            new_stage = next(stage for stage in stages if stage.position == horizon)
            before = old._horizon_note(study_timeline=timeline, horizon_stage_index=horizon)
            after = new_module._horizon_note(study_timeline=timeline, horizon_stage=new_stage)
            if before != after:
                problems.append(f"заметка горизонта разошлась: {timeline} / {horizon}")
            if old_stage["title"] != new_stage.title:
                problems.append(f"заголовок этапа {horizon} разошёлся")
    return problems


async def check_entity_shape(stages: list[CourseStage]) -> list[str]:
    """Проверить, что сущности собраны деревом, а не плоским списком.

    Args:
        stages: Этапы, прочитанные репозиторием.

    Returns:
        Список замечаний; пустой, если дерево собрано верно.
    """
    problems: list[str] = []
    for stage in stages:
        if not isinstance(stage, CourseStage):
            problems.append(f"этап {stage.position} не CourseStage")
        for module in stage.modules:
            if not isinstance(module, CourseModule):
                problems.append(f"модуль {module.id} не CourseModule")
            for topic in module.topics:
                if not isinstance(topic, CourseTopic):
                    problems.append(f"тема {topic.id} не CourseTopic")
        if [module.position for module in stage.modules] != sorted(
            module.position for module in stage.modules
        ):
            problems.append(f"этап {stage.position}: модули не по порядку")
        for module in stage.modules:
            if [topic.position for topic in module.topics] != sorted(
                topic.position for topic in module.topics
            ):
                problems.append(f"модуль {module.id}: темы не по порядку")
    return problems


async def main() -> None:
    """Прогнать все проверки и напечатать итог."""
    old = load_old_module()
    stage_rows, module_rows, topic_rows = load_migration_rows()

    data_problems = check_rows_match_old_roadmap(old, stage_rows, module_rows, topic_rows)
    stages = await seed_and_read(stage_rows, module_rows, topic_rows)
    shape_problems = await check_entity_shape(stages)
    render_problems = await compare(old, stages)

    print(f"rows: stages={len(stage_rows)} modules={len(module_rows)} topics={len(topic_rows)}")
    print(f"read back from sqlite: stages={len(stages)}")
    print(f"data vs _ROADMAP   : {len(data_problems)} расхождений")
    print(f"entity tree shape  : {len(shape_problems)} расхождений")
    print(f"rendered plan diff : {len(render_problems)} расхождений")

    for label, problems in (
        ("DATA", data_problems),
        ("SHAPE", shape_problems),
        ("RENDER", render_problems),
    ):
        for problem in problems[:10]:
            print(f"  {label}: {problem}")

    total = len(data_problems) + len(shape_problems) + len(render_problems)
    print("RESULT:", "IDENTICAL" if total == 0 else f"{total} MISMATCHES")
    if total:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
