"""Generic-CRUD база для репозиториев."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base import Base

M = TypeVar("M", bound=Base)


class BaseRepo(Generic[M]):
    model: type[M]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: int) -> M | None:
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: M) -> M:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: M) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def all(self) -> list[M]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())