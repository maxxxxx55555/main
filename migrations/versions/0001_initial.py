"""initial schema: users, messages, payments, knowledge_base

Revision ID: 0001
Revises:
Create Date: 2026-09-21

Совместимо с SQLite (dev) и PostgreSQL (prod):
- PK: BIGINT c variant INTEGER для sqlite (rowid autoincrement)
- timestamps: timezone=True; на SQLite хранятся naive-UTC (единая политика app)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

BigIntPk = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("plan", sa.String(16), nullable=False, server_default="free"),
        sa.Column("messages_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("period_reset_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tz", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_tg_id", "users", ["tg_id"], unique=True)

    op.create_table(
        "messages",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("user_id", BigIntPk, nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_user_created", "messages", ["user_id", "created_at"])

    op.create_table(
        "payments",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("user_id", BigIntPk, nullable=False),
        sa.Column("plan", sa.String(16), nullable=False),
        sa.Column("amount_stars", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("telegram_payment_charge_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        # UNIQUE inline: идемпотентность платежей (§5.3); SQLite не умеет ALTER-констрейнты
        sa.UniqueConstraint("telegram_payment_charge_id", name="uq_payments_charge_id"),
    )
    op.create_index("ix_payments_user", "payments", ["user_id", "created_at"])

    op.create_table(
        "knowledge_base",
        sa.Column("id", BigIntPk, primary_key=True, autoincrement=True),
        sa.Column("owner_id", BigIntPk, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_knowledge_base_owner_id", "knowledge_base", ["owner_id"])


def downgrade() -> None:
    op.drop_table("knowledge_base")
    op.drop_table("payments")
    op.drop_table("messages")
    op.drop_table("users")