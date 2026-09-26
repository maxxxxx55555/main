"""Репо для лидов и фидбэка."""
from __future__ import annotations

import datetime as dt
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.lead import Lead, Feedback


class LeadRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def capture(
        self,
        user_id: int,
        name: str | None = None,
        contact: str | None = None,
        interest: str = "General",
        score: int = 50,
        notes: str = "",
    ) -> Lead:
        lead = Lead(
            user_id=user_id,
            name=name,
            contact=contact,
            interest=interest,
            score=score,
            notes=notes,
        )
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def recent(self, limit: int = 50) -> Sequence[Lead]:
        stmt = select(Lead).order_by(Lead.captured_at.desc()).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def stats(self) -> dict[str, int | float]:
        result = {
            "total": (await self.session.execute(select(func.count(Lead.id)))).scalar_one(),
            "avg_score": (
                await self.session.execute(select(func.avg(Lead.score)))
            ).scalar() or 0,
        }
        return result