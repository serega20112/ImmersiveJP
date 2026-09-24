"""Справочник областей навыков диагностики.

До появления таблицы диагностика и план общались русскими строками: список
`skill_label` в банках вопросов и отдельная таблица «просадка -> этап» в сборке
плана. Здесь эта связь становится данными, а идентификатор навыка перестаёт
зависеть от переименования.

Revision ID: 20260923_0002
Revises: 20260923_0001
Create Date: 2026-09-23 13:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260923_0002"
down_revision = "20260923_0001"
branch_labels = None
depends_on = None

SKILL_AREA_ROWS = [{'id': 1,
  'code': 'hiragana',
  'title': 'Хирагана',
  'stage_position': 0,
  'coaching_tip': 'Сначала прочитай строки по ромадзи, потом повтори без подсказки.'},
 {'id': 2,
  'code': 'basic-vocabulary',
  'title': 'Базовая лексика',
  'stage_position': 2,
  'coaching_tip': None},
 {'id': 3,
  'code': 'polite-formulas',
  'title': 'Формулы вежливости',
  'stage_position': 2,
  'coaching_tip': None},
 {'id': 4,
  'code': 'particles',
  'title': 'Частицы',
  'stage_position': 1,
  'coaching_tip': 'Проговаривай предложения с акцентом на частицы и меняй одно '
                  'существительное.'},
 {'id': 5,
  'code': 'basic-sentence-order',
  'title': 'Базовый порядок предложения',
  'stage_position': 1,
  'coaching_tip': 'Читай диалоги по ролям и отдельно отмечай тему, действие и объект.'},
 {'id': 6,
  'code': 'word-reading',
  'title': 'Чтение слов',
  'stage_position': 0,
  'coaching_tip': None},
 {'id': 7,
  'code': 'polite-request',
  'title': 'Вежливая просьба',
  'stage_position': 2,
  'coaching_tip': None},
 {'id': 8,
  'code': 'negative-form',
  'title': 'Отрицательная форма',
  'stage_position': 1,
  'coaching_tip': None},
 {'id': 9,
  'code': 'daily-scenes',
  'title': 'Бытовые сцены',
  'stage_position': 2,
  'coaching_tip': None},
 {'id': 10,
  'code': 'speech-register',
  'title': 'Регистр речи',
  'stage_position': 5,
  'coaching_tip': None},
 {'id': 11,
  'code': 'phrase-cohesion',
  'title': 'Связность фразы',
  'stage_position': 4,
  'coaching_tip': None},
 {'id': 12,
  'code': 'kanji-in-context',
  'title': 'Чтение канжи в контексте',
  'stage_position': 5,
  'coaching_tip': None},
 {'id': 13,
  'code': 'intention-and-plan',
  'title': 'Намерение и план',
  'stage_position': 4,
  'coaching_tip': None},
 {'id': 14,
  'code': 'accuracy-in-context',
  'title': 'Точность в контексте',
  'stage_position': 4,
  'coaching_tip': None},
 {'id': 15, 'code': 'katakana', 'title': 'Катакана', 'stage_position': 0, 'coaching_tip': None}]

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
