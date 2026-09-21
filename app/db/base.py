"""Асинхронный движок и фабрика сессий (SQLite dev / PostgreSQL prod)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import BASE_DIR, get_settings
from app.db.models import Base


def build_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or settings.database_url
    kwargs: dict = {"echo": False}
    if url.startswith("sqlite"):
        # Гарантируем существование каталога под SQLite-файл
        db_path = url.split("///", 1)[-1]
        if db_path and db_path != ":memory:":
            Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
    else:
        kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def create_all(engine: AsyncEngine) -> None:
    """MVP: DDL через create_all. Прод — alembic (см. README, roadmap)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)