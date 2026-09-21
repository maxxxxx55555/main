"""Фикстуры: SQLite in-memory + MockProvider — без внешних зависимостей."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db.models import Base


@pytest.fixture
def settings() -> Settings:
    return Settings(
        bot_token="",
        llm_api_key="",
        database_url="sqlite+aiosqlite://",
        free_limit=2,
        pro_limit=5,
        business_limit=10,
        pro_price_stars=100,
        business_price_stars=250,
        period_days=30,
        embedding_dim=64,
        context_window=4,
        context_token_budget=200,
    )


@pytest.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s