"""Глобальный обработчик ошибок: лог + вежливое уведомление пользователя.

Гарантии:
- ни одна ошибка хэндлера не остаётся без записи в логе (traceback пишется целиком);
- пользователь получает один понятный текст (с анти-спам-паузой на чат);
- ошибки уведомления (заблокировал бота, кривой chat_id) не эскалируются.
"""

from __future__ import annotations

import logging
import time

from aiogram import Bot
from aiogram.types import ErrorEvent, Message

from app.config import Settings

logger = logging.getLogger(__name__)

_NOTIFY_COOLDOWN_S = 120.0
_last_notify: dict[int, float] = {}

GENERIC_ERROR = (
    "⚠️ Упс, что-то пошло не так. Я уже записал детали и разберусь.\n"
    "Попробуйте ещё раз через минуту."
)


def _support_suffix(settings: Settings) -> str:
    username = settings.support_username.strip().lstrip("@")
    if not username:
        return ""
    return f"\n\nЕсли повторяется — напишите в поддержку: @{username}"


def _chat_id_from(event: ErrorEvent) -> int | None:
    update = event.update
    message = update.message or update.edited_message
    if message is not None:
        return message.chat.id
    callback = update.callback_query
    if callback is not None and callback.message is not None:
        return callback.message.chat.id
    return None


def _should_notify(chat_id: int, now: float | None = None) -> bool:
    current = time.monotonic() if now is None else now
    previous = _last_notify.get(chat_id)
    if previous is not None and current - previous < _NOTIFY_COOLDOWN_S:
        return False
    _last_notify[chat_id] = current
    if len(_last_notify) > 10_000:  # защита от роста словаря на большом трафике
        cutoff = current - _NOTIFY_COOLDOWN_S
        for key in [k for k, ts in _last_notify.items() if ts < cutoff]:
            _last_notify.pop(key, None)
    return True


async def on_error(event: ErrorEvent, bot: Bot | None = None, settings: Settings | None = None) -> bool:
    """Обработчик `dp.errors`: логирует исключение и уведомляет пользователя."""
    exc = event.exception
    logger.exception("Необработанная ошибка в хэндлере: %s: %s", type(exc).__name__, exc)

    chat_id = _chat_id_from(event)
    if chat_id is None or bot is None or not _should_notify(chat_id):
        return True

    text = GENERIC_ERROR
    if settings is not None:
        text += _support_suffix(settings)

    try:
        sent: Message = await bot.send_message(chat_id, text)
        logger.info("Пользователь уведомлён об ошибке (chat_id=%s, msg_id=%s)", chat_id, sent.message_id)
    except Exception:  # ошибки уведомления не эскалируем
        logger.warning("Не удалось уведомить пользователя об ошибке (chat_id=%s)", chat_id, exc_info=True)
    return True