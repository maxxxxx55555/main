"""Фоновое обслуживание БД: retention-политика сообщений (§9.4).

История диалогов нужна только для контекста (последние N сообщений), поэтому
старые записи удаляются — меньше данных, меньше риска, быстрее бэкапы.
Пользователь может удалить всё сам командой /forget_me в любой момент.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repo.messages import MessageRepo

logger = logging.getLogger(__name__)

FIRST_RUN_DELAY_S = 60  # не мешаем старту: первый прогон через минуту


async def purge_once(
    sessionmaker: async_sessionmaker[AsyncSession], retention_days: int
) -> int:
    """Удаляет сообщения старше retention_days. Возвращает число удалённых."""
    if retention_days <= 0:
        return 0
    async with sessionmaker() as session:
        deleted = await MessageRepo(session).purge_older_than(retention_days)
        await session.commit()
    if deleted:
        logger.info("Retention: удалено сообщений старше %s дн.: %s", retention_days, deleted)
    return deleted


async def retention_loop(
    sessionmaker: async_sessionmaker[AsyncSession],
    retention_days: int,
    interval_hours: int = 24,
) -> None:
    """Бесконечная задача: прогон retention раз в interval_hours (отменяется на shutdown)."""
    if retention_days <= 0:
        logger.info("Retention отключён (RETENTION_DAYS=0)")
        return
    try:
        await asyncio.sleep(FIRST_RUN_DELAY_S)
        while True:
            try:
                await purge_once(sessionmaker, retention_days)
            except Exception:  # фоновой задаче нельзя умирать
                logger.exception("Retention-прогон завершился ошибкой")
            await asyncio.sleep(interval_hours * 3600)
    except asyncio.CancelledError:
        logger.info("Retention-задача остановлена")
        raise