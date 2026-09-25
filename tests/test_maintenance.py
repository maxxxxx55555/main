"""Retention-политика: удаление старых сообщений (services/maintenance.py)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.base import utcnow
from app.db.models.message import Message
from app.db.repo.messages import MessageRepo
from app.db.repo.users import UserRepo
from app.services.maintenance import purge_once


def _maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def test_purge_once_removes_only_old_messages(engine):
    maker = _maker(engine)
    async with maker() as session:
        user = await UserRepo(session).get_or_create(1)
        await MessageRepo(session).add_message(user.id, "user", "старое")
        await session.execute(
            update(Message).values(created_at=utcnow() - dt.timedelta(days=100))
        )
        await MessageRepo(session).add_message(user.id, "user", "свежее")
        await session.commit()

    deleted = await purge_once(maker, retention_days=90)
    assert deleted == 1

    async with maker() as session:
        rows = await MessageRepo(session).recent(user.id, limit=10)
        assert [row.content for row in rows] == ["свежее"]


async def test_purge_once_noop_when_disabled(engine):
    maker = _maker(engine)
    async with maker() as session:
        user = await UserRepo(session).get_or_create(2)
        await MessageRepo(session).add_message(user.id, "user", "текст")
        await session.execute(
            update(Message).values(created_at=utcnow() - dt.timedelta(days=999))
        )
        await session.commit()

    assert await purge_once(maker, retention_days=0) == 0
    async with maker() as session:
        assert len(await MessageRepo(session).recent(user.id, limit=10)) == 1


async def test_purge_once_empty_db_returns_zero(engine):
    assert await purge_once(_maker(engine), retention_days=30) == 0
