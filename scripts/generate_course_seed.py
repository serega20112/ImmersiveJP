"""Генерация миграции с учебной программой и её seed-данными.

Одноразовый инструмент. Читает актуальный _ROADMAP и пишет файл ревизии
Alembic с полным содержимым — DDL трёх таблиц и 118 строк справочных
данных. Данные закладываются литералом намеренно: ревизия обязана оставаться
воспроизводимой после того, как _ROADMAP исчезнет из кода. Соответственно,
после переноса roadmap в базу этот скрипт становится неработоспособным и
хранится только как запись того, откуда взялись данные.

Использование:
    python scripts/generate_course_seed.py
"""

from __future__ import annotations

import pprint
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.application.use_cases.profile import build_learning_plan as plan_module

REVISION = "20260923_0001"
DOWN_REVISION = "673036106712"
CREATE_DATE = "2026-09-23 12:00:00"
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "build"
    / "alembic"
    / "versions"
    / f"{REVISION}_course_program.py"
)

STAGE_CODES: dict[int, str] = {
    0: "base",
    1: "basic-grammar",
    2: "first-speech",
    3: "kanji",
    4: "solid-base",
    5: "intermediate",
    6: "advanced",
    7: "final",
}

MODULE_SLUGS: dict[tuple[int, str], str] = {
    (0, "Хирагана"): "hiragana",
    (0, "Катакана"): "katakana",
    (0, "Чтение"): "reading",
    (1, "Предложения"): "sentences",
    (1, "Частицы"): "particles",
    (1, "Глаголы"): "verbs",
    (1, "Словарь"): "vocabulary",
    (2, "Глаголы"): "te-form",
    (2, "Прилагательные"): "adjectives",
    (2, "Простые диалоги"): "dialogues",
    (2, "Словарь"): "vocabulary",
    (3, "Базовые кандзи"): "basic-kanji",
    (3, "Чтения"): "readings",
    (3, "Письмо"): "writing",
    (4, "Грамматика"): "grammar",
    (4, "Слушание"): "listening",
    (4, "Чтение"): "reading",
    (4, "Словарь"): "vocabulary",
    (5, "Кандзи"): "kanji",
    (5, "Грамматика"): "grammar",
    (5, "Разговор"): "conversation",
    (5, "Погружение"): "immersion",
    (6, "Кандзи"): "kanji",
    (6, "Речь"): "speech",
    (6, "Понимание"): "comprehension",
    (6, "Письмо"): "writing",
    (7, "Свобода использования"): "fluency",
}


def build_rows() -> tuple[list[dict], list[dict], list[dict]]:
    """Разложить _ROADMAP на строки трёх таблиц.

    Returns:
        Кортеж из списков этапов, модулей и тем с псевдо-идентификаторами.

    Raises:
        KeyError: Если для этапа или модуля не задан код.
    """
    stage_rows: list[dict] = []
    module_rows: list[dict] = []
    topic_rows: list[dict] = []

    for stage in plan_module._ROADMAP:
        index = stage["index"]
        stage_code = STAGE_CODES[index]
        stage_rows.append(
            {
                "id": index + 1,
                "code": stage_code,
                "title": stage["title"],
                "timeframe": stage["timeframe"],
                "summary": stage["summary"],
                "position": index,
            }
        )

        for module_position, (title, items) in enumerate(stage["modules"], start=1):
            slug = MODULE_SLUGS[(index, title)]
            module_id = index * 100 + module_position
            module_rows.append(
                {
                    "id": module_id,
                    "stage_id": index + 1,
                    "code": f"{stage_code}.{slug}",
                    "title": title,
                    "position": module_position,
                }
            )
            for topic_position, item in enumerate(items, start=1):
                topic_rows.append(
                    {
                        "id": module_id * 100 + topic_position,
                        "module_id": module_id,
                        "title": item,
                        "position": topic_position,
                    }
                )

    return stage_rows, module_rows, topic_rows


def check_unique(rows: list[dict], key: str, label: str) -> None:
    """Проверить уникальность колонки и упасть при дубле.

    Args:
        rows: Список строк таблицы.
        key: Проверяемый ключ.
        label: Название таблицы для сообщения об ошибке.

    Raises:
        ValueError: Если значение ключа встречается более одного раза.
    """
    seen: set[str] = set()
    for row in rows:
        value = row[key]
        if value in seen:
            raise ValueError(f"Дубль {label}.{key}: {value}")
        seen.add(value)


def render_literal(name: str, rows: list[dict]) -> str:
    """Отрендерить список строк как присваивание литерала Python.

    Args:
        name: Имя константы.
        rows: Строки таблицы.

    Returns:
        Текст присваивания с многострочным литералом.
    """
    return f"{name} = " + pprint.pformat(rows, width=96, sort_dicts=False) + "\n"


def render_migration(
    stage_rows: list[dict], module_rows: list[dict], topic_rows: list[dict]
) -> str:
    """Собрать полный исходный текст ревизии Alembic.

    Args:
        stage_rows: Строки таблицы этапов.
        module_rows: Строки таблицы модулей.
        topic_rows: Строки таблицы тем.

    Returns:
        Текст файла миграции.
    """
    header = f'''"""Учебная программа: этапы, модули и темы.

Вместе со схемой заполняется справочное содержимое, взятое из бывшего
захардкоженного roadmap. Идентификаторы задаются явно, чтобы ревизия
оставалась воспроизводимой и работала в офлайн-режиме alembic --sql.

Revision ID: {REVISION}
Revises: {DOWN_REVISION}
Create Date: {CREATE_DATE}
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "{REVISION}"
down_revision = "{DOWN_REVISION}"
branch_labels = None
depends_on = None

'''

    tables = '''_COURSE_STAGES = sa.table(
    "course_stages",
    sa.column("id", sa.Integer),
    sa.column("code", sa.String),
    sa.column("title", sa.String),
    sa.column("timeframe", sa.String),
    sa.column("summary", sa.String),
    sa.column("position", sa.Integer),
)

_COURSE_MODULES = sa.table(
    "course_modules",
    sa.column("id", sa.Integer),
    sa.column("stage_id", sa.Integer),
    sa.column("code", sa.String),
    sa.column("title", sa.String),
    sa.column("position", sa.Integer),
)

_COURSE_TOPICS = sa.table(
    "course_topics",
    sa.column("id", sa.Integer),
    sa.column("module_id", sa.Integer),
    sa.column("title", sa.String),
    sa.column("position", sa.Integer),
)


def upgrade() -> None:
    """Создать таблицы учебной программы и заполнить их справочными данными."""
    op.create_table(
        "course_stages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("timeframe", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_course_stages_code"),
        sa.UniqueConstraint("position", name="uq_course_stages_position"),
    )
    op.create_index(op.f("ix_course_stages_code"), "course_stages", ["code"], unique=True)
    op.create_table(
        "course_modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["stage_id"], ["course_stages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_course_modules_code"),
        sa.UniqueConstraint("stage_id", "position", name="uq_course_modules_stage_position"),
    )
    op.create_index(op.f("ix_course_modules_code"), "course_modules", ["code"], unique=True)
    op.create_index(op.f("ix_course_modules_stage_id"), "course_modules", ["stage_id"], unique=False)
    op.create_table(
        "course_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["course_modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "position", name="uq_course_topics_module_position"),
    )
    op.create_index(op.f("ix_course_topics_module_id"), "course_topics", ["module_id"], unique=False)

    op.bulk_insert(_COURSE_STAGES, STAGE_ROWS)
    op.bulk_insert(_COURSE_MODULES, MODULE_ROWS)
    op.bulk_insert(_COURSE_TOPICS, TOPIC_ROWS)

    for table_name in ("course_stages", "course_modules", "course_topics"):
        op.execute(
            "SELECT setval("
            f"pg_get_serial_sequence('{table_name}', 'id'), "
            f"(SELECT MAX(id) FROM {table_name}))"
        )


def downgrade() -> None:
    """Удалить таблицы учебной программы."""
    op.drop_index(op.f("ix_course_topics_module_id"), table_name="course_topics")
    op.drop_table("course_topics")
    op.drop_index(op.f("ix_course_modules_stage_id"), table_name="course_modules")
    op.drop_index(op.f("ix_course_modules_code"), table_name="course_modules")
    op.drop_table("course_modules")
    op.drop_index(op.f("ix_course_stages_code"), table_name="course_stages")
    op.drop_table("course_stages")
'''

    body = "\n".join(
        [
            render_literal("STAGE_ROWS", stage_rows),
            render_literal("MODULE_ROWS", module_rows),
            render_literal("TOPIC_ROWS", topic_rows),
        ]
    )
    return header + body + "\n" + tables


def main() -> None:
    """Сгенерировать файл ревизии и напечатать сводку по данным."""
    if OUTPUT_PATH.exists():
        raise SystemExit(f"Ревизия уже существует: {OUTPUT_PATH}")

    stage_rows, module_rows, topic_rows = build_rows()
    check_unique(stage_rows, "code", "course_stages")
    check_unique(stage_rows, "position", "course_stages")
    check_unique(module_rows, "code", "course_modules")
    check_unique(topic_rows, "id", "course_topics")

    longest_summary = max(len(row["summary"]) for row in stage_rows)
    longest_topic = max(len(row["title"]) for row in topic_rows)
    longest_module_code = max(len(row["code"]) for row in module_rows)

    OUTPUT_PATH.write_text(render_migration(stage_rows, module_rows, topic_rows), encoding="utf-8")

    print(f"записано: {OUTPUT_PATH.name}")
    print(
        f"stages={len(stage_rows)} modules={len(module_rows)} topics={len(topic_rows)} "
        f"rows={len(stage_rows) + len(module_rows) + len(topic_rows)}"
    )
    print(
        f"longest summary={longest_summary}, topic title={longest_topic}, module code={longest_module_code}"
    )


if __name__ == "__main__":
    main()
