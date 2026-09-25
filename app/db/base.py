"""Асинхронный движок, фабрика сессий и применение Alembic-миграций.

Схема БД управляется исключительно Alembic: `app.main` вызывает `run_migrations()`
до старта polling/webhook. Это исключает конфликт `metadata.create_all()` с
миграциями (таблицы создаются дважды) и гарантирует одинаковую схему в dev и prod.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import BASE_DIR, get_settings


def _ensure_sqlite_dir(url: str) -> None:
    """Каталог под SQLite-файл должен существовать до подключения/миграций."""
    if not url.startswith("sqlite"):
        return
    db_path = url.split("///", 1)[-1]
    if db_path and db_path != ":memory:":
        Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)


def build_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or settings.database_url
    kwargs: dict = {"echo": False}
    if url.startswith("sqlite"):
        _ensure_sqlite_dir(url)
    else:
        kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def run_migrations() -> None:
    """Применяет Alembic-миграции до `head` (синхронно; вызывать в отдельном потоке).

    URL берётся из настроек — как в migrations/env.py, поэтому мигрируется ровно
    та БД, к которой подключится приложение. Повторный вызов безопасен:
    на актуальной схеме Alembic не выполняет никаких операций.
    """
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "migrations"))
    _ensure_sqlite_dir(get_settings().database_url)
    command.upgrade(config, "head")