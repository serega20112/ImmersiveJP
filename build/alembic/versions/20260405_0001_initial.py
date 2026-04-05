"""initial schema

Revision ID: 20260405_0001
Revises: None
Create Date: 2026-04-05 15:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260405_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("learning_goal", sa.String(length=32), nullable=True),
        sa.Column("language_level", sa.String(length=32), nullable=True),
        sa.Column("interests_json", sa.JSON(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "learning_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("track", sa.String(length=32), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("examples_json", sa.JSON(), nullable=False),
        sa.Column("key_terms_json", sa.JSON(), nullable=False),
        sa.Column("batch_number", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "track", "batch_number", "position", name="uq_learning_cards_position"),
    )
    op.create_index("ix_learning_cards_user_id", "learning_cards", ["user_id"])
    op.create_index("ix_learning_cards_track", "learning_cards", ["track"])

    op.create_table(
        "card_completions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("card_id", sa.Integer(), sa.ForeignKey("learning_cards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "card_id", name="uq_card_completion_user_card"),
    )
    op.create_index("ix_card_completions_user_id", "card_completions", ["user_id"])
    op.create_index("ix_card_completions_card_id", "card_completions", ["card_id"])

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("track", sa.String(length=32), nullable=False),
        sa.Column("last_generated_batch", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "track", name="uq_learning_session_user_track"),
    )
    op.create_index("ix_learning_sessions_user_id", "learning_sessions", ["user_id"])
    op.create_index("ix_learning_sessions_track", "learning_sessions", ["track"])


def downgrade() -> None:
    op.drop_index("ix_learning_sessions_track", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_user_id", table_name="learning_sessions")
    op.drop_table("learning_sessions")
    op.drop_index("ix_card_completions_card_id", table_name="card_completions")
    op.drop_index("ix_card_completions_user_id", table_name="card_completions")
    op.drop_table("card_completions")
    op.drop_index("ix_learning_cards_track", table_name="learning_cards")
    op.drop_index("ix_learning_cards_user_id", table_name="learning_cards")
    op.drop_table("learning_cards")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
