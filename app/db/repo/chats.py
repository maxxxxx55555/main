"""Репо для настроек чатов и активности участников (Group Chat Bot)."""

from __future__ import annotations

import datetime as dt
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatMemberActivity, ChatSettings


class ChatRepo:
    """CRUD для настроек групповых чатов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, chat_id: int, title: str = "") -> ChatSettings:
        settings = await self.session.get(ChatSettings, chat_id)
        if settings is None:
            settings = ChatSettings(chat_id=chat_id, title=title)
            self.session.add(settings)
            await self.session.flush()
        if title and title != settings.title:
            settings.title = title
        return settings

    async def get(self, chat_id: int) -> ChatSettings | None:
        return await self.session.get(ChatSettings, chat_id)

    async def update_rules(self, chat_id: int, rules: str) -> ChatSettings:
        settings = await self.session.get(ChatSettings, chat_id)
        if settings is None:
            settings = ChatSettings(chat_id=chat_id, title="")
            self.session.add(settings)
            await self.session.flush()
        settings.rules = rules
        await self.session.flush()
        return settings

    async def update_welcome(self, chat_id: int, message: str, enabled: bool = True) -> ChatSettings:
        settings = await self.session.get(ChatSettings, chat_id)
        if settings is None:
            settings = ChatSettings(chat_id=chat_id, title="")
            self.session.add(settings)
            await self.session.flush()
        if message:
            settings.welcome_message = message
        settings.welcome_enabled = enabled
        await self.session.flush()
        return settings

    async def toggle_anti_spam(self, chat_id: int, enabled: bool) -> ChatSettings:
        settings = await self.session.get(ChatSettings, chat_id)
        if settings is None:
            settings = ChatSettings(chat_id=chat_id, title="")
            self.session.add(settings)
            await self.session.flush()
        settings.anti_spam_enabled = enabled
        await self.session.flush()
        return settings


class ActivityRepo:
    """Отслеживание активности участников группы для рейтингов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_message(
        self, chat_id: int, user_id: int, username: str | None = "", first_name: str | None = ""
    ) -> None:
        """Увеличить счётчики активности для участника."""
        activity = await self.session.scalar(
            select(ChatMemberActivity).where(
                ChatMemberActivity.chat_id == chat_id,
                ChatMemberActivity.user_id == user_id,
            )
        )
        if activity is None:
            activity = ChatMemberActivity(
                chat_id=chat_id,
                user_id=user_id,
                username=username or "",
                first_name=first_name or "",
                message_count=1,
                score=1,
            )
            self.session.add(activity)
        else:
            activity.message_count += 1
            activity.score += 1
            if username and not activity.username:
                activity.username = username
            if first_name and not activity.first_name:
                activity.first_name = first_name
        activity.last_active = dt.datetime.now(dt.UTC)
        await self.session.flush()

    async def top_users(self, chat_id: int, limit: int = 10) -> Sequence[ChatMemberActivity]:
        stmt = (
            select(ChatMemberActivity)
            .where(ChatMemberActivity.chat_id == chat_id)
            .order_by(ChatMemberActivity.score.desc())
            .limit(limit)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def chat_stats(self, chat_id: int) -> dict[str, int]:
        """Агрегированная статистика чата."""
        total_messages = (
            await self.session.execute(
                select(func.sum(ChatMemberActivity.message_count)).where(
                    ChatMemberActivity.chat_id == chat_id
                )
            )
        ).scalar() or 0

        active_users = (
            await self.session.execute(
                select(func.count(func.distinct(ChatMemberActivity.user_id))).where(
                    ChatMemberActivity.chat_id == chat_id
                )
            )
        ).scalar_one()

        week_ago = dt.datetime.now(dt.UTC) - dt.timedelta(days=7)
        active_week = (
            await self.session.execute(
                select(func.count(func.distinct(ChatMemberActivity.user_id))).where(
                    ChatMemberActivity.chat_id == chat_id,
                    ChatMemberActivity.last_active >= week_ago,
                )
            )
        ).scalar_one()

        return {
            "total_messages": total_messages,
            "active_users": active_users,
            "active_week": active_week,
        }

    async def reset_activity(self, chat_id: int) -> None:
        """Сбросить активность всех участников чата."""
        await self.session.execute(
            update(ChatMemberActivity)
            .where(ChatMemberActivity.chat_id == chat_id)
            .values(message_count=0, score=0)
        )
