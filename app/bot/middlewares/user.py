"""get_or_create пользователя и injection в контекст хэндлера."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.user import User
from app.db.repo.users import UserRepo


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        session: AsyncSession | None = data.get("session")
        if tg_user is not None and not tg_user.is_bot and session is not None:
            settings: Settings = data["settings"]
            user: User = await UserRepo(session).get_or_create(
                tg_id=tg_user.id, tz=settings.default_tz
            )
            data["user"] = user
        return await handler(event, data)