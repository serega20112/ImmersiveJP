"""Учебная программа: этапы, модули и темы.

Вместе со схемой заполняется справочное содержимое, взятое из бывшего
захардкоженного roadmap. Идентификаторы задаются явно, чтобы ревизия
оставалась воспроизводимой и работала в офлайн-режиме alembic --sql.

Revision ID: 20260923_0001
Revises: 673036106712
Create Date: 2026-09-23 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260923_0001"
down_revision = "673036106712"
branch_labels = None
depends_on = None

STAGE_ROWS = [{'id': 1,
  'code': 'base',
  'title': 'База',
  'timeframe': '0-1 месяц',
  'summary': 'Сначала ставится фундамент чтения и распознавания базовых слогов. Без этого '
             'дальше идти бессмысленно: грамматика и речь будут разваливаться на каждом новом '
             'шаге.',
  'position': 0},
 {'id': 2,
  'code': 'basic-grammar',
  'title': 'Базовая грамматика',
  'timeframe': '1-3 месяц',
  'summary': 'Здесь собирается каркас предложения: тема, объект, отрицание, вопросы и базовые '
             'глагольные формы. Это этап, где язык перестает быть списком слов.',
  'position': 1},
 {'id': 3,
  'code': 'first-speech',
  'title': 'Начало речи',
  'timeframe': '3-6 месяц',
  'summary': 'На этом этапе язык начинает работать в коротких сценах: просьба, магазин, '
             'знакомство, бытовой диалог. Важно не просто помнить форму, а быстро доставать ее '
             'в ситуации.',
  'position': 2},
 {'id': 4,
  'code': 'kanji',
  'title': 'Кандзи',
  'timeframe': 'параллельно с этапа 2',
  'summary': 'Кандзи не должны ждать идеального момента. Как только базовая речь пошла, чтение '
             'и письмо постепенно подхватываются параллельной дорожкой.',
  'position': 3},
 {'id': 5,
  'code': 'solid-base',
  'title': 'Уверенный базис',
  'timeframe': '6-12 месяц',
  'summary': 'Этап, где базовые формы связываются в устойчивую практику: слушание, чтение и '
             'грамматика начинают работать вместе, а не по отдельности.',
  'position': 4},
 {'id': 6,
  'code': 'intermediate',
  'title': 'Средний уровень',
  'timeframe': '1-2 год',
  'summary': 'Здесь уже строится речь без постоянной опоры на заготовки. Добавляются сложные '
             'формы, больше кандзи и настоящее погружение в живой материал.',
  'position': 5},
 {'id': 7,
  'code': 'advanced',
  'title': 'Продвинутый',
  'timeframe': '2-3 год',
  'summary': 'На этом уровне язык уже используется как инструмент: для разговора, понимания '
             'длинных форматов, письма и переключения между стилями.',
  'position': 6},
 {'id': 8,
  'code': 'final',
  'title': 'Финал',
  'timeframe': 'после 3 лет и дальше',
  'summary': 'Финальный этап не про очередной набор тем, а про устойчивую жизнь в языке: '
             'понимание без перевода, свободная речь и самостоятельное расширение словаря.',
  'position': 7}]

MODULE_ROWS = [{'id': 1, 'stage_id': 1, 'code': 'base.hiragana', 'title': 'Хирагана', 'position': 1},
 {'id': 2, 'stage_id': 1, 'code': 'base.katakana', 'title': 'Катакана', 'position': 2},
 {'id': 3, 'stage_id': 1, 'code': 'base.reading', 'title': 'Чтение', 'position': 3},
 {'id': 101,
  'stage_id': 2,
  'code': 'basic-grammar.sentences',
  'title': 'Предложения',
  'position': 1},
 {'id': 102,
  'stage_id': 2,
  'code': 'basic-grammar.particles',
  'title': 'Частицы',
  'position': 2},
 {'id': 103, 'stage_id': 2, 'code': 'basic-grammar.verbs', 'title': 'Глаголы', 'position': 3},
 {'id': 104,
  'stage_id': 2,
  'code': 'basic-grammar.vocabulary',
  'title': 'Словарь',
  'position': 4},
 {'id': 201, 'stage_id': 3, 'code': 'first-speech.te-form', 'title': 'Глаголы', 'position': 1},
 {'id': 202,
  'stage_id': 3,
  'code': 'first-speech.adjectives',
  'title': 'Прилагательные',
  'position': 2},
 {'id': 203,
  'stage_id': 3,
  'code': 'first-speech.dialogues',
  'title': 'Простые диалоги',
  'position': 3},
 {'id': 204,
  'stage_id': 3,
  'code': 'first-speech.vocabulary',
  'title': 'Словарь',
  'position': 4},
 {'id': 301,
  'stage_id': 4,
  'code': 'kanji.basic-kanji',
  'title': 'Базовые кандзи',
  'position': 1},
 {'id': 302, 'stage_id': 4, 'code': 'kanji.readings', 'title': 'Чтения', 'position': 2},
 {'id': 303, 'stage_id': 4, 'code': 'kanji.writing', 'title': 'Письмо', 'position': 3},
 {'id': 401, 'stage_id': 5, 'code': 'solid-base.grammar', 'title': 'Грамматика', 'position': 1},
 {'id': 402, 'stage_id': 5, 'code': 'solid-base.listening', 'title': 'Слушание', 'position': 2},
 {'id': 403, 'stage_id': 5, 'code': 'solid-base.reading', 'title': 'Чтение', 'position': 3},
 {'id': 404, 'stage_id': 5, 'code': 'solid-base.vocabulary', 'title': 'Словарь', 'position': 4},
 {'id': 501, 'stage_id': 6, 'code': 'intermediate.kanji', 'title': 'Кандзи', 'position': 1},
 {'id': 502,
  'stage_id': 6,
  'code': 'intermediate.grammar',
  'title': 'Грамматика',
  'position': 2},
 {'id': 503,
  'stage_id': 6,
  'code': 'intermediate.conversation',
  'title': 'Разговор',
  'position': 3},
 {'id': 504,
  'stage_id': 6,
  'code': 'intermediate.immersion',
  'title': 'Погружение',
  'position': 4},
 {'id': 601, 'stage_id': 7, 'code': 'advanced.kanji', 'title': 'Кандзи', 'position': 1},
 {'id': 602, 'stage_id': 7, 'code': 'advanced.speech', 'title': 'Речь', 'position': 2},
 {'id': 603,
  'stage_id': 7,
  'code': 'advanced.comprehension',
  'title': 'Понимание',
  'position': 3},
 {'id': 604, 'stage_id': 7, 'code': 'advanced.writing', 'title': 'Письмо', 'position': 4},
 {'id': 701,
  'stage_id': 8,
  'code': 'final.fluency',
  'title': 'Свобода использования',
  'position': 1}]

TOPIC_ROWS = [{'id': 101, 'module_id': 1, 'title': 'символы', 'position': 1},
 {'id': 102, 'module_id': 1, 'title': 'дакутэн и хандакутэн', 'position': 2},
 {'id': 103, 'module_id': 1, 'title': 'сочетания вроде きゃ / しゃ', 'position': 3},
 {'id': 104, 'module_id': 1, 'title': 'маленькое つ', 'position': 4},
 {'id': 201, 'module_id': 2, 'title': 'символы', 'position': 1},
 {'id': 202, 'module_id': 2, 'title': 'долгие гласные ー', 'position': 2},
 {'id': 203, 'module_id': 2, 'title': 'удвоение ッ', 'position': 3},
 {'id': 204, 'module_id': 2, 'title': 'иностранные сочетания вроде ファ / ティ', 'position': 4},
 {'id': 301, 'module_id': 3, 'title': 'простые слова', 'position': 1},
 {'id': 302, 'module_id': 3, 'title': 'чтение вслух', 'position': 2},
 {'id': 303, 'module_id': 3, 'title': 'ритм коротких фраз', 'position': 3},
 {'id': 10101, 'module_id': 101, 'title': 'A は B です', 'position': 1},
 {'id': 10102, 'module_id': 101, 'title': 'вопросы с か', 'position': 2},
 {'id': 10103, 'module_id': 101, 'title': 'отрицание じゃないです', 'position': 3},
 {'id': 10201, 'module_id': 102, 'title': 'は как тема', 'position': 1},
 {'id': 10202, 'module_id': 102, 'title': 'が как субъект', 'position': 2},
 {'id': 10203, 'module_id': 102, 'title': 'を как объект', 'position': 3},
 {'id': 10204, 'module_id': 102, 'title': 'に для времени и направления', 'position': 4},
 {'id': 10205, 'module_id': 102, 'title': 'の для принадлежности', 'position': 5},
 {'id': 10301, 'module_id': 103, 'title': 'ます-форма', 'position': 1},
 {'id': 10302, 'module_id': 103, 'title': 'отрицание', 'position': 2},
 {'id': 10303, 'module_id': 103, 'title': 'прошедшее время', 'position': 3},
 {'id': 10401, 'module_id': 104, 'title': 'бытовой словарь до ~300 слов', 'position': 1},
 {'id': 10402, 'module_id': 104, 'title': 'частые существительные и глаголы', 'position': 2},
 {'id': 20101, 'module_id': 201, 'title': 'て-форма', 'position': 1},
 {'id': 20102, 'module_id': 201, 'title': 'просьбы через ください', 'position': 2},
 {'id': 20103, 'module_id': 201, 'title': 'разрешение через いいです', 'position': 3},
 {'id': 20104, 'module_id': 201, 'title': 'запрет через だめ', 'position': 4},
 {'id': 20201, 'module_id': 202, 'title': 'い-прилагательные', 'position': 1},
 {'id': 20202, 'module_id': 202, 'title': 'な-прилагательные', 'position': 2},
 {'id': 20203, 'module_id': 202, 'title': 'прошедшие и отрицательные формы', 'position': 3},
 {'id': 20301, 'module_id': 203, 'title': 'знакомство', 'position': 1},
 {'id': 20302, 'module_id': 203, 'title': 'магазин', 'position': 2},
 {'id': 20303, 'module_id': 203, 'title': 'повседневные сцены', 'position': 3},
 {'id': 20401, 'module_id': 204, 'title': 'расширение до ~800 слов', 'position': 1},
 {'id': 20402, 'module_id': 204, 'title': 'частые бытовые конструкции', 'position': 2},
 {'id': 30101, 'module_id': 301, 'title': 'числа', 'position': 1},
 {'id': 30102, 'module_id': 301, 'title': 'время', 'position': 2},
 {'id': 30103, 'module_id': 301, 'title': 'частые базовые слова', 'position': 3},
 {'id': 30201, 'module_id': 302, 'title': 'онъёми', 'position': 1},
 {'id': 30202, 'module_id': 302, 'title': 'кунъёми', 'position': 2},
 {'id': 30203, 'module_id': 302, 'title': 'контекстный выбор чтения', 'position': 3},
 {'id': 30301, 'module_id': 303, 'title': 'порядок черт', 'position': 1},
 {'id': 30302, 'module_id': 303, 'title': 'ручная практика', 'position': 2},
 {'id': 30303, 'module_id': 303, 'title': 'распознавание в словах', 'position': 3},
 {'id': 40101, 'module_id': 401, 'title': 'ている', 'position': 1},
 {'id': 40102, 'module_id': 401, 'title': 'たい', 'position': 2},
 {'id': 40103, 'module_id': 401, 'title': 'つもり', 'position': 3},
 {'id': 40104, 'module_id': 401, 'title': 'ことができる', 'position': 4},
 {'id': 40201, 'module_id': 402, 'title': 'аниме с разбором', 'position': 1},
 {'id': 40202, 'module_id': 402, 'title': 'подкасты', 'position': 2},
 {'id': 40203, 'module_id': 402, 'title': 'повторение фраз вслух', 'position': 3},
 {'id': 40301, 'module_id': 403, 'title': 'простые тексты', 'position': 1},
 {'id': 40302, 'module_id': 403, 'title': 'короткие диалоги', 'position': 2},
 {'id': 40303, 'module_id': 403, 'title': 'привычка читать без ромадзи', 'position': 3},
 {'id': 40401, 'module_id': 404, 'title': 'расширение до ~1500 слов', 'position': 1},
 {'id': 40402, 'module_id': 404, 'title': 'бытовые и учебные темы', 'position': 2},
 {'id': 50101, 'module_id': 501, 'title': '~1000 знаков', 'position': 1},
 {'id': 50102, 'module_id': 501, 'title': 'чтение в реальном контексте', 'position': 2},
 {'id': 50201, 'module_id': 502, 'title': 'условные формы なら / たら', 'position': 1},
 {'id': 50202, 'module_id': 502, 'title': 'пассив', 'position': 2},
 {'id': 50203, 'module_id': 502, 'title': 'каузатив', 'position': 3},
 {'id': 50204, 'module_id': 502, 'title': 'сложные конструкции', 'position': 4},
 {'id': 50301, 'module_id': 503, 'title': 'свободные диалоги', 'position': 1},
 {'id': 50302, 'module_id': 503, 'title': 'выражение мыслей', 'position': 2},
 {'id': 50303, 'module_id': 503, 'title': 'ответы без долгой паузы', 'position': 3},
 {'id': 50401, 'module_id': 504, 'title': 'аниме без сабов', 'position': 1},
 {'id': 50402, 'module_id': 504, 'title': 'манга', 'position': 2},
 {'id': 50403, 'module_id': 504, 'title': 'игры', 'position': 3},
 {'id': 60101, 'module_id': 601, 'title': '~2000+ знаков', 'position': 1},
 {'id': 60102,
  'module_id': 601,
  'title': 'быстрое чтение без постоянной расшифровки',
  'position': 2},
 {'id': 60201, 'module_id': 602, 'title': 'беглая разговорная речь', 'position': 1},
 {'id': 60202, 'module_id': 602, 'title': 'сленг', 'position': 2},
 {'id': 60203, 'module_id': 602, 'title': 'переключение между стилями', 'position': 3},
 {'id': 60301, 'module_id': 603, 'title': 'фильмы', 'position': 1},
 {'id': 60302, 'module_id': 603, 'title': 'интервью', 'position': 2},
 {'id': 60303, 'module_id': 603, 'title': 'живое общение', 'position': 3},
 {'id': 60401, 'module_id': 604, 'title': 'тексты', 'position': 1},
 {'id': 60402, 'module_id': 604, 'title': 'сообщения', 'position': 2},
 {'id': 60403, 'module_id': 604, 'title': 'практическая переписка', 'position': 3},
 {'id': 70101, 'module_id': 701, 'title': 'свободный разговор', 'position': 1},
 {'id': 70102, 'module_id': 701, 'title': 'понимание без постоянного перевода', 'position': 2},
 {'id': 70103, 'module_id': 701, 'title': 'жизнь в языковой среде', 'position': 3}]

_COURSE_STAGES = sa.table(
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
