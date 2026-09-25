"""Антифлуд: token bucket в памяти (§8.4). Redis — в prod-профиле.

Особенности:
- администраторы не ограничиваются;
- пользователь получает одно мягкое предупреждение на окно (а не тишину);
- устаревшие записи периодически вычищаются — словарь не растёт бесконечно.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.bot.texts import THROTTLE_WARNING
from app.config import Settings

logger = logging.getLogger(__name__)

_CLEANUP_EVERY = 500  # вызовов между чистками словарей


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.limit = max(settings.rate_limit_per_minute, 1)
        self.window = 60.0
        self._hits: dict[int, deque[float]] = defaultdict(deque)
        self._warned: dict[int, float] = {}
        self._calls = 0

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None or tg_user.id in data["settings"].admin_id_set:
            return await handler(event, data)

        now = time.monotonic()
        self._calls += 1
        if self._calls % _CLEANUP_EVERY == 0:
            self._cleanup(now)

        bucket = self._hits[tg_user.id]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            await self._warn_once(tg_user.id, event, now)
            return None
        bucket.append(now)
        return await handler(event, data)

    async def _warn_once(self, user_id: int, event: TelegramObject, now: float) -> None:
        """Одно предупреждение на окно: пользователь понимает, почему молчит бот."""
        if now - self._warned.get(user_id, 0.0) < self.window:
            return
        self._warned[user_id] = now
        try:
            if isinstance(event, Message):
                await event.answer(THROTTLE_WARNING)
            elif isinstance(event, CallbackQuery):
                await event.answer(THROTTLE_WARNING, show_alert=False)
        except Exception:  # noqa: BLE001 — предупреждение не должно ломать апдейт
            logger.debug("Не удалось отправить предупреждение о флуде (user_id=%s)", user_id)

    def _cleanup(self, now: float) -> None:
        stale = [
            user_id
            for user_id, bucket in self._hits.items()
            if not bucket or now - bucket[-1] > self.window
        ]
        for user_id in stale:
            self._hits.pop(user_id, None)
        old_warned = [uid for uid, ts in self._warned.items() if now - ts > self.window]
        for user_id in old_warned:
            self._warned.pop(user_id, None)
        if stale or old_warned:
            logger.debug("Throttle cleanup: -%s hits, -%s warnings", len(stale), len(old_warned))