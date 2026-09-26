"""Добавление таблиц: leads, feedback (premium lead-capture + rating system).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-26

Совместимо с SQLite и PostgreSQL.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

BigIntPk = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("user_id", BigIntPk, nullable=False),
        sa.Column("name", sa.String(128), nullable=True),
        sa.Column("contact", sa.String(255), nullable=True),
        sa.Column("interest", sa.String(255), nullable=False, server_default="General"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("source", sa.String(64), nullable=False, server_default="chat"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_leads_user_id", "leads", ["user_id"])

    op.create_table(
        "feedback",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("user_id", BigIntPk, nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False, server_default=""),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("leads")