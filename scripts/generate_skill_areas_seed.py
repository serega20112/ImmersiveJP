"""Генерация миграции со справочником учебных навыков.

Одноразовый инструмент. Собирает области навыков из двух мест, которые до
этого жили отдельно и сверялись по строке: список `skill_label` из
диагностических банков и таблица «просадка -> этап» из сборки плана. Результат
— ревизия Alembic с таблицей skill_areas и её seed-данными.

Отсутствующий код или неиспользованная строка считаются ошибкой генерации,
чтобы справочник не начал расходиться с диагностикой молча.

Использование (из корня репозитория):
    python -m scripts.generate_skill_areas_seed
"""

from __future__ import annotations

import pprint
from datetime import date
from pathlib import Path

from src.application.use_cases.onboarding.diagnostic_questions import _DIAGNOSTIC_BANKS
from src.application.use_cases.profile.build_learning_plan import _WEAK_POINT_STAGES

REVISION = "20260923_0002"
DOWN_REVISION = "20260923_0001"
CREATE_DATE = f"{date(2026, 9, 23).isoformat()} 13:00:00"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "build" / "alembic" / "versions" / f"{REVISION}_skill_areas.py"

SKILL_AREA_CODES: dict[str, str] = {
    "Хирагана": "hiragana",
    "Катакана": "katakana",
    "Чтение слов": "word-reading",
    "Базовая лексика": "basic-vocabulary",
    "Формулы вежливости": "polite-formulas",
    "Частицы": "particles",
    "Базовый порядок предложения": "basic-sentence-order",
    "Отрицательная форма": "negative-form",
    "Вежливая просьба": "polite-request",
    "Бытовые сцены": "daily-scenes",
    "Регистр речи": "speech-register",
    "Связность фразы": "phrase-cohesion",
    "Чтение канжи в контексте": "kanji-in-context",
    "Намерение и план": "intention-and-plan",
    "Точность в контексте": "accuracy-in-context",
}

SKILL_AREA_TIPS: dict[str, str] = {
    "hiragana": "Сначала прочитай строки по ромадзи, потом повтори без подсказки.",
    "particles": "Проговаривай предложения с акцентом на частицы и меняй одно существительное.",
    "basic-sentence-order": "Читай диалоги по ролям и отдельно отмечай тему, действие и объект.",
}


def diagnostic_labels() -> list[str]:
    """Собрать все заголовки навыков, которые выдаёт диагностика.

    Returns:
        Уникальные заголовки в порядке их появления в банках вопросов.
    """
    labels: list[str] = []
    for bank in _DIAGNOSTIC_BANKS.values():
        for question in bank["questions"]:
            label = question["skill_label"]
            if label not in labels:
                labels.append(label)
    return labels


def stage_by_label() -> dict[str, int]:
    """Развернуть таблицу «просадка -> этап» в вид «заголовок -> этап».

    Returns:
        Словарь заголовка навыка от позиции этапа.

    Raises:
        ValueError: Если один заголовок приписан двум этапам.
    """
    mapping: dict[str, int] = {}
    for stage_position, labels in _WEAK_POINT_STAGES:
        for label in labels:
            if label in mapping and mapping[label] != stage_position:
                raise ValueError(f"Заголовок '{label}' смотрит на два этапа")
            mapping[label] = stage_position
    return mapping


def build_rows() -> list[dict]:
    """Собрать строки справочника областей навыков.

    Проверяет, что словарь кодов и диагностика описывают друг друга полностью:
    лишний код не создаёт навыков, пропущенный — падает ошибкой.

    Returns:
        Список строк таблицы skill_areas.

    Raises:
        ValueError: Если заголовок диагностики не имеет кода или код не
            встречается в диагностике.
    """
    labels = diagnostic_labels()
    stages = stage_by_label()

    unknown = sorted(set(labels) - set(SKILL_AREA_CODES))
    if unknown:
        raise ValueError(f"Для навыков нет кодов: {unknown}")
    stale = sorted(set(SKILL_AREA_CODES) - set(labels) - set(stages))
    if stale:
        raise ValueError(f"Коды не соответствуют ни диагностике, ни этапам: {stale}")

    ordered = labels + sorted(set(stages) - set(labels))
    rows: list[dict] = []
    for position, label in enumerate(ordered, start=1):
        code = SKILL_AREA_CODES[label]
        rows.append(
            {
                "id": position,
                "code": code,
                "title": label,
                "stage_position": stages.get(label),
                "coaching_tip": SKILL_AREA_TIPS.get(code),
            }
        )
    return rows


def render_migration(rows: list[dict]) -> str:
    """Собрать полный исходный текст ревизии Alembic.

    Args:
        rows: Строки справочника областей навыков.

    Returns:
        Текст файла миграции.
    """
    header = f'''"""Справочник областей навыков диагностики.

До появления таблицы диагностика и план общались русскими строками: список
`skill_label` в банках вопросов и отдельная таблица «просадка -> этап» в сборке
плана. Здесь эта связь становится данными, а идентификатор навыка перестаёт
зависеть от переименования.

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

SKILL_AREA_ROWS = {pprint.pformat(rows, width=96, sort_dicts=False)}

_SKILL_AREAS = sa.table(
    "skill_areas",
    sa.column("id", sa.Integer),
    sa.column("code", sa.String),
    sa.column("title", sa.String),
    sa.column("stage_position", sa.Integer),
    sa.column("coaching_tip", sa.String),
)


def upgrade() -> None:
    """Создать справочник областей навыков и заполнить его."""
    op.create_table(
        "skill_areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("stage_position", sa.Integer(), nullable=True),
        sa.Column("coaching_tip", sa.String(length=400), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_skill_areas_code"),
        sa.UniqueConstraint("title", name="uq_skill_areas_title"),
        sa.ForeignKeyConstraint(
            ["stage_position"],
            ["course_stages.position"],
            name="fk_skill_areas_stage_position",
            ondelete="SET NULL",
        ),
    )
    op.create_index(op.f("ix_skill_areas_code"), "skill_areas", ["code"], unique=True)

    op.bulk_insert(_SKILL_AREAS, SKILL_AREA_ROWS)
    op.execute(
        "SELECT setval("
        "pg_get_serial_sequence('skill_areas', 'id'), "
        "(SELECT MAX(id) FROM skill_areas))"
    )


def downgrade() -> None:
    """Удалить справочник областей навыков."""
    op.drop_index(op.f("ix_skill_areas_code"), table_name="skill_areas")
    op.drop_table("skill_areas")
'''
    return header


def main() -> None:
    """Сгенерировать файл ревизии и напечатать сводку."""
    if OUTPUT_PATH.exists():
        raise SystemExit(f"Ревизия уже существует: {OUTPUT_PATH}")

    rows = build_rows()
    codes = [row["code"] for row in rows]
    if len(set(codes)) != len(codes):
        raise SystemExit("Коды областей навыков не уникальны")

    OUTPUT_PATH.write_text(render_migration(rows), encoding="utf-8")

    with_stage = sum(1 for row in rows if row["stage_position"] is not None)
    with_tip = sum(1 for row in rows if row["coaching_tip"])
    print(f"записано: {OUTPUT_PATH.name}")
    print(f"areas={len(rows)} со ссылкой на этап={with_stage} с подсказкой={with_tip}")


if __name__ == "__main__":
    main()
