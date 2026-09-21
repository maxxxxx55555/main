"""Роутер: агрегация хэндлеров в порядке приоритета."""

from __future__ import annotations

from aiogram import Router

from app.bot.handlers import admin, chat, knowledge, payments, start


def build_router() -> Router:
    router = Router(name="root")
    # Порядок важен: платежи → админка → команды → база знаний (FSM) → чат (catch-all)
    router.include_router(payments.router)
    router.include_router(admin.router)
    router.include_router(start.router)
    router.include_router(knowledge.router)
    router.include_router(chat.router)
    return router