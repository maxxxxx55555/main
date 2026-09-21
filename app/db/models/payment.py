import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, utcnow
from app.db.models.user import BigIntPk


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_user", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPk, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_stars: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    # Ключ идемпотентности (UNIQUE) — защита от повторной активации
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )