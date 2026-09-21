"""Антифлуд: token bucket в памяти (§8.4). Redis — в prod-профиле."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import Settings


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self.limit = settings.rate_limit_per_minute
        self.window = 60.0
        self._hits: dict[int, deque[float]] = defaultdict(deque)

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
        bucket = self._hits[tg_user.id]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return  # тихо дропаем флуд
        bucket.append(now)
        return await handler(event, data)