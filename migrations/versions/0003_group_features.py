"""Добавление таблиц: chat_settings, chat_activity (Group Chat Bot).

Features: moderation, anti-spam, user ratings, welcome messages.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-26

Совместимо с SQLite и PostgreSQL.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

BigIntPk = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "chat_settings",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False, server_default=""),
        sa.Column("welcome_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("welcome_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("rules", sa.Text(), nullable=False, server_default=""),
        sa.Column("anti_spam_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("delete_service_messages", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("warn_threshold", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("mute_duration_min", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("auto_moderate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "chat_activity",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", BigIntPk, nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(128), nullable=True),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chat_settings.chat_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_activity_chat_user", "chat_activity", ["chat_id", "user_id"])
    op.create_index("ix_chat_activity_score", "chat_activity", ["chat_id", "score"])


def downgrade() -> None:
    op.drop_table("chat_activity")
    op.drop_table("chat_settings")
