"""Хелперы отправки сообщений: безопасные edit/send для любых состояний UI.

Два контракта текста (не смешивать!):
- **authored** (`send_authored`, `safe_edit`): текст из app/bot/texts.py — уже готовый
  Telegram-HTML, динамические вставки экранированы на месте; повторного экранирования нет.
- **external** (`send_llm`): сырой текст извне (ответ LLM) — экранируется и конвертируется
  markdown-lite → HTML, длинные тексты разбиваются на несколько сообщений.

Оба пути гарантируют: пользователь получит сообщение, даже если Telegram отверг
HTML-разметку (fallback — plain text).
"""

from __future__ import annotations

import logging

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    ReplyKeyboardMarkup,
)

from app.utils.text import SAFE_MESSAGE_LIMIT, format_reply

logger = logging.getLogger(__name__)

_NO_PREVIEW = LinkPreviewOptions(is_disabled=True)
AnyKeyboard = InlineKeyboardMarkup | ReplyKeyboardMarkup | None


def _split_authored(text: str, limit: int = SAFE_MESSAGE_LIMIT) -> list[str]:
    """Разбиение авторского HTML: только по границам абзацев (теги не рвём)."""
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    buffer = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(candidate) > limit and buffer:
            parts.append(buffer)
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        parts.append(buffer)
    return parts


async def _answer(message: Message, text: str, markup: AnyKeyboard = None) -> None:
    try:
        await message.answer(text, reply_markup=markup, link_preview_options=_NO_PREVIEW)
    except TelegramBadRequest:
        logger.warning("Telegram отклонил HTML-разметку, отправляю как plain text")
        await message.answer(text, reply_markup=markup, parse_mode=None)


async def send_authored(message: Message, text: str, reply_markup: AnyKeyboard = None) -> None:
    """Отправка авторского HTML (texts.py): без экранирования, разбиение по абзацам."""
    parts = _split_authored(text)
    last = len(parts) - 1
    for index, part in enumerate(parts):
        await _answer(message, part, reply_markup if index == last else None)


async def send_llm(message: Message, text: str, reply_markup: AnyKeyboard = None) -> None:
    """Отправка внешнего текста (LLM): экранирование → markdown-lite → разбиение ≤4096."""
    parts = format_reply(text, SAFE_MESSAGE_LIMIT) or [""]
    last = len(parts) - 1
    for index, part in enumerate(parts):
        await _answer(message, part, reply_markup if index == last else None)


async def safe_edit(
    message: Message | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Редактирует сообщение (авторский HTML); при невозможности — отправляет новое."""
    if message is None:
        return
    try:
        await message.edit_text(text, reply_markup=reply_markup, link_preview_options=_NO_PREVIEW)
        return
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        logger.debug("safe_edit: редактирование невозможно (%s), отправляю новое", exc)
    except Exception:  # UI не должен падать из-за гонок/удалённых сообщений
        logger.debug("safe_edit: неожиданная ошибка редактирования", exc_info=True)
    await _answer(message, text, reply_markup)