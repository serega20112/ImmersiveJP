"""Состояние генерации партии карточек в учебных сессиях.

Партия перестаёт создаваться одним блокирующим запросом: она бронируется до
обращения к модели и дописывается карточка за карточкой фоном. Страница должна
отличать «готово» от «ещё генерируется» и «сорвалось», а переживать перезапуск
процесса и перезагрузку страницы такое состояние может только хранясь в базе.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260923_0003_batch_generation"
down_revision = "20260923_0002_skill_areas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Добавить колонки состояния генерации партии."""
    op.add_column(
        "learning_sessions",
        sa.Column(
            "generation_state",
            sa.String(length=16),
            server_default=sa.text("'ready'"),
            nullable=False,
        ),
    )
    op.add_column(
        "learning_sessions",
        sa.Column(
            "generation_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Удалить колонки состояния генерации партии."""
    op.drop_column("learning_sessions", "generation_started_at")
    op.drop_column("learning_sessions", "generation_state")
