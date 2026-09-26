"""Модель: групповые чаты и настройки бота внутри них (Group Chat Bot).

Таблицы:
- chat_settings: настройки каждого чата (приветствие, правила, анти-спам)
- chat_activity: счётчики активности участников для рейтингов

Premium features: auto-moderation, anti-spam, user ratings, welcome messages.
"""

import datetime as dt

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.sqlite import INTEGER as SQLITE_INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, utcnow
from app.db.models.user import BigIntPk


class ChatSettings(Base):
    """Настройки бота в конкретном чате (группе или супергруппе)."""
    __tablename__ = "chat_settings"

    chat_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="Telegram chat_id (отрицательный для групп)"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="Название чата")
    welcome_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Приветствовать новых участников"
    )
    welcome_message: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Кастомное приветственное сообщение"
    )
    rules: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="Правила чата")
    anti_spam_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Автоматическая блокировка спама"
    )
    delete_service_messages: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Удалять сервисные сообщения (join/leave)"
    )
    warn_threshold: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, comment="Кол-во варнов до автоматического mute"
    )
    mute_duration_min: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, comment="Мьют в минутах при превышении порога варнов"
    )
    auto_moderate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Автоматически удалять спам-сообщения"
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False,
        onupdate=utcnow,
    )


class ChatMemberActivity(Base):
    """Счётчики активности участника в чате для рейтингов."""
    __tablename__ = "chat_activity"
    __table_args__ = (
        Index("ix_chat_activity_chat_user", "chat_id", "user_id"),
        Index("ix_chat_activity_score", "chat_id", "score"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chat_settings.chat_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigIntPk, nullable=False, comment="Telegram user_id участника"
    )
    username: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    first_name: Mapped[str] = mapped_column(String(128), nullable=True, default="")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Баллы активности")
    last_active: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
