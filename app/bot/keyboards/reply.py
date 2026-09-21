"""Reply-кнопки быстрых действий."""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def quick_actions() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="💬 Задать вопрос")
    kb.button(text="⭐️ Тарифы")
    kb.adjust(2)
    return kb.as_markup()