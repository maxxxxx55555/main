"""Точка входа: сборка (engine, storage, dispatcher, сервисы) и запуск polling.

Запуск: python -m app.main  (или ai-employee после pip install -e .)
Webhook-режим — по roadmap (docs/ARCHITECTURE.md §10, этап 2).
"""

from __future__ import annotations

import asyncio
import logging
import signal

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.middlewares.db import DbSessionMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.middlewares.user import UserMiddleware
from app.bot.router import build_router
from app.config import get_settings
from app.db.base import build_engine, build_sessionmaker, create_all
from app.services.ai.provider import build_provider
from app.services.ai.rag import RagService
from app.services.billing.plans import PlanCatalog
from app.services.billing.stars import StarsBillingService
from app.services.limits.usage import UsageService
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


async def run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и укажите токен от @BotFather."
        )

    setup_logging()
    logger.info("Запуск AI-Сотрудника (mock_llm=%s)", settings.use_mock_llm)

    # --- Инфраструктура ---
    engine = build_engine()
    await create_all(engine)
    sessionmaker = build_sessionmaker(engine)

    storage = MemoryStorage()
    if settings.redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            storage = RedisStorage.from_url(settings.redis_url)
            logger.info("FSM storage: Redis")
        except ImportError:
            logger.warning("redis не установлен — FSM в MemoryStorage (§8.3)")

    # --- Сервисы ---
    provider = build_provider(settings)
    catalog = PlanCatalog(settings)
    usage = UsageService(catalog, settings.period_days)
    billing = StarsBillingService(catalog, settings)
    rag = RagService(provider, settings)

    # --- Dispatcher ---
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Зависимости, доступные всем хэндлерам
    dp["settings"] = settings
    dp["catalog"] = catalog
    dp["usage"] = usage
    dp["billing"] = billing
    dp["rag"] = rag
    dp["provider"] = provider

    # Middlewares: порядок важен (сессия → пользователь → флуд)
    db_mw = DbSessionMiddleware(sessionmaker)
    for observer in (dp.message, dp.callback_query, dp.pre_checkout_query):
        observer.middleware(db_mw)
        observer.middleware(UserMiddleware())
        observer.middleware(ThrottlingMiddleware(settings))

    dp.include_router(build_router())

    # --- Graceful shutdown (§8.5) ---
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:  # Windows
            pass

    polling_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    logger.info("Бот запущен (long polling). Ctrl+C для остановки.")
    await stop_event.wait()
    polling_task.cancel()
    await polling_task
    await bot.session.close()
    await engine.dispose()
    logger.info("Бот остановлен.")


def main() -> None:
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()