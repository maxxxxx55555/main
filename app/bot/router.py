"""Роутер: агрегация хэндлеров в порядке приоритета.

Порядок важен: платежи -> админка -> команды -> база знаний (FSM) -> меню -> чат.
Специфичные фильтры всегда раньше общих.
"""

from __future__ import annotations

from aiogram import Router


def _clone_router(source: Router, name: str) -> Router:
    """Клонирует хэндлеры модульного роутера в независимый экземпляр.

    Aiogram разрешает подключить один Router только к одному родителю. В тестах,
    при hot-reload и повторной сборке dispatcher один и тот же модульный роутер
    может понадобиться несколько раз, поэтому создаём новый Router и переносим
    в него зарегистрированные HandlerObject без изменения бизнес-логики.
    """
    target = Router(name=name)
    for event_name, source_observer in source.observers.items():
        target_observer = target.observers[event_name]
        target_observer.handlers.extend(source_observer.handlers)
        if source_observer._handler.filters:
            target_observer._handler.filters.extend(source_observer._handler.filters)
        for middleware in source_observer.middleware:
            target_observer.middleware(middleware)
        for middleware in source_observer.outer_middleware:
            target_observer.outer_middleware(middleware)
    return target


def build_router() -> Router:
    """Создаёт новый root-роутер с хэндлерами в порядке приоритета."""
    router = Router(name="root")
    from app.bot.handlers import admin, chat, knowledge, menu, payments, start

    router.include_router(_clone_router(payments.router, "payments"))
    router.include_router(_clone_router(admin.router, "admin"))
    router.include_router(_clone_router(start.router, "start"))
    router.include_router(_clone_router(knowledge.router, "knowledge"))
    router.include_router(_clone_router(menu.router, "menu"))
    router.include_router(_clone_router(chat.router, "chat"))
    return router
