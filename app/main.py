"""Точка входа: сборка (engine, storage, dispatcher, сервисы) и запуск.

Режимы (WEBHOOK_MODE в .env):
- False (по умолчанию): long polling + локальный health-сервер /health
- True: aiohttp-сервер на WEBAPP_PORT — приём апдейтов
  {WEBHOOK_BASE_URL}/{WEBHOOK_SECRET_PATH} + /health (ARCHITECTURE.md §9.3, §10)

Запуск: python -m app.main  (или ai-employee после pip install -e .)
Миграции: alembic upgrade head
"""

from __future__ import annotations

import asyncio
import contextlib
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
from app.db.base import build_engine, build_sessionmaker
from app.services.ai.provider import build_provider
from app.services.ai.rag import RagService
from app.services.billing.plans import PlanCatalog
from app.services.billing.stars import StarsBillingService
from app.services.limits.usage import UsageService
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def _build_dispatcher(settings) -> tuple[Dispatcher, Bot]:
    """Сборка dispatcher, middlewares и зависимостей (общая для polling/webhook)."""
    storage = MemoryStorage()
    if settings.redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage

            storage = RedisStorage.from_url(settings.redis_url)
            logger.info("FSM storage: Redis")
        except ImportError:
            logger.warning("redis не установлен — FSM в MemoryStorage (§8.3)")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    catalog = PlanCatalog(settings)
    dp["settings"] = settings
    dp["catalog"] = catalog
    dp["usage"] = UsageService(catalog, settings.period_days)
    dp["billing"] = StarsBillingService(catalog, settings)
    dp["provider"] = build_provider(settings)
    dp["rag"] = RagService(dp["provider"], settings)

    db_mw = DbSessionMiddleware(build_sessionmaker(build_engine()))
    for observer in (dp.message, dp.callback_query, dp.pre_checkout_query):
        observer.middleware(db_mw)
        observer.middleware(UserMiddleware())
        observer.middleware(ThrottlingMiddleware(settings))

    dp.include_router(build_router())
    return dp, bot


async def start_webapp(
    host: str, port: int, webhook_path: str | None, dp: Dispatcher, bot: Bot,
    webhook_secret: str | None = None,
):
    """aiohttp-сервер: /health всегда + webhook-роут при webhook-режиме."""
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler
    from aiohttp import web

    app = web.Application()

    if webhook_path:
        SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=webhook_secret).register(
            app, path=webhook_path
        )

    async def health(_request: web.Request) -> web.Response:
        # Лёгкая проверка живости; при недоступности БД LB уводит трафик (§8.3)
        return web.json_response({"status": "ok", "mode": "webhook" if webhook_path else "polling"})

    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    return runner


async def run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и укажите токен от @BotFather."
        )

    setup_logging()
    logger.info("Запуск AI-Сотрудника (mock_llm=%s, mode=%s)",
                settings.use_mock_llm, "webhook" if settings.webhook_mode else "polling")

    # DDL: dev — create_all (просто); prod — alembic upgrade head (см. DEPLOY.md)
    from app.db.base import create_all

    engine = build_engine()
    await create_all(engine)

    dp, bot = _build_dispatcher(settings)

    # --- Graceful shutdown (§8.5) ---
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):  # Windows
            loop.add_signal_handler(sig, stop_event.set)

    webhook_path = None
    runner = None
    if settings.webhook_mode:
        if not settings.webhook_base_url:
            raise SystemExit("WEBHOOK_MODE=1 требует WEBHOOK_BASE_URL (https://домен)")
        webhook_path = f"/{settings.webhook_secret_path.strip('/')}"
        webhook_url = f"{settings.webhook_base_url.rstrip('/')}{webhook_path}"
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.webhook_secret_token or None,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info("Webhook установлен: %s", webhook_url)

    runner = await start_webapp(
        settings.webapp_host, settings.webapp_port, webhook_path, dp, bot,
        webhook_secret=settings.webhook_secret_token or None,
    )

    if settings.webhook_mode:
        logger.info("Webhook-сервер слушает :%s%s", settings.webapp_port, webhook_path)
        await stop_event.wait()
        with contextlib.suppress(Exception):
            await bot.delete_webhook(drop_pending_updates=False)
    else:
        logger.info("Бот запущен (long polling). /health на :%s. Ctrl+C — остановка.",
                    settings.webapp_port)
        polling = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
        await stop_event.wait()
        polling.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await polling

    await runner.cleanup()
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