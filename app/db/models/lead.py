"""Модель: захваченные лиды из диалогов (Lead Capture). Premium feature."""
import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, utcnow
from app.db.models.user import BigIntPk


class Lead(Base):
    """Автоматически захваченные лиды: имя, контакт, интерес, источник."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPk, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    contact: Mapped[str] = mapped_column(String(255), nullable=True)
    interest: Mapped[str] = mapped_column(String(255), nullable=True, default="General")
    score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 0-100
    source: Mapped[str] = mapped_column(String(64), default="chat", nullable=False)
    captured_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Feedback(Base):
    """Feedback от пользователей после диалогов."""
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntPk, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )