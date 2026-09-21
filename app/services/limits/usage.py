"""Проверка лимита и атомарное списание usage (§4.2)."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repo.users import UserRepo
from app.services.billing.plans import PlanCatalog


class LimitExceeded(Exception):
    """Семантика HTTP 429: лимит периода исчерпан. LLM не вызывается."""

    def __init__(self, reset_at: dt.datetime) -> None:
        self.reset_at = reset_at
        super().__init__(f"Limit exceeded, resets at {reset_at}")


class UsageService:
    def __init__(self, catalog: PlanCatalog, period_days: int) -> None:
        self.catalog = catalog
        self.period_days = period_days

    async def consume(self, session: AsyncSession, user: User) -> int:
        """Ленивый сброс + атомарное списание одного сообщения.

        Возвращает остаток сообщений. Бросает LimitExceeded, если 0 строк
        обновлено (гонки параллельных сообщений исключены).
        """
        await UserRepo(session).reset_if_needed(user, self.period_days)
        limit = self.catalog.limit_for(user.plan)

        result = await session.execute(
            update(User)
            .where(User.id == user.id, User.messages_used < limit)
            .values(messages_used=User.messages_used + 1)
        )
        if result.rowcount != 1:
            raise LimitExceeded(reset_at=user.period_reset_at)

        await session.refresh(user)
        return max(limit - user.messages_used, 0)

    async def refund(self, session: AsyncSession, user: User) -> None:
        """Возврат одного списания при отказе LLM (§8.3: лимиты не списываются)."""
        await session.execute(
            update(User)
            .where(User.id == user.id, User.messages_used > 0)
            .values(messages_used=User.messages_used - 1)
        )
        await session.refresh(user)

    @staticmethod
    def warning_suffix(remaining: int, limit: int, reset_at: dt.datetime) -> str:
        """Мягкие уведомления 80% / 100% (§4.4) — не блокируют ответ."""
        date = reset_at.strftime("%d.%m.%Y")
        if remaining == 0:
            return f"\n\n⚠️ Это было последнее сообщение периода. Лимит обновится {date}."
        if remaining <= max(limit // 5, 1):  # ≤ 20% остатка
            return f"\n\nℹ️ Осталось {remaining} сообщений до {date}."
        return ""
