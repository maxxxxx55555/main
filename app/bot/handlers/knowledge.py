"""/knowledge — загрузка базы знаний (RAG) для платных тарифов."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import knowledge_kb
from app.bot.states import KnowledgeStates
from app.config import Settings
from app.db.models.user import User
from app.services.ai.rag import RagService

router = Router(name="knowledge")
logger = logging.getLogger(__name__)

NEED_PLAN = "📚 База знаний доступна на тарифах PRO и Business. Подключите в разделе тарифов."


@router.callback_query(F.data == "knowledge")
async def cb_knowledge(callback: CallbackQuery, user: User) -> None:
    can_upload = user.plan != "free"
    if callback.message is not None:
        await callback.message.edit_text(
            "📚 <b>База знаний</b>\n\n"
            "Загрузите FAQ, цены, условия работы, скрипты продаж — бот будет "
            "отвечать клиентам строго по этим данным.\n"
            "Отправьте текст одним сообщением (до 4000 символов).",
            reply_markup=knowledge_kb(can_upload),
        )
    await callback.answer()


@router.callback_query(F.data == "knowledge_add")
async def cb_knowledge_add(
    callback: CallbackQuery, state: FSMContext, user: User
) -> None:
    if user.plan == "free":
        await callback.answer(NEED_PLAN, show_alert=True)
        return
    await state.set_state(KnowledgeStates.waiting_text)
    if callback.message is not None:
        await callback.message.edit_text(
            "📚 Отправьте текст базы знаний одним сообщением.\n\n"
            "<i>Например: «Мы кофейня на Ленина 5. Работаем 8:00-22:00. Капучино — 250₽…»</i>\n\n"
            "Для отмены: /cancel"
        )
    await callback.answer()


@router.message(KnowledgeStates.waiting_text, F.text)
async def save_knowledge(
    message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    rag: RagService,
    settings: Settings,
) -> None:
    assert message.text is not None
    if len(message.text) > settings.max_message_len:
        await message.answer("✋ Слишком длинный текст. Разбейте на части.")
        return
    added = await rag.add_text(session, user.id, message.text)
    await state.clear()
    await message.answer(
        f"✅ Сохранено чанков знаний: <b>{added}</b>.\n"
        "Теперь бот будет отвечать клиентам по этим данным. Задайте тестовый вопрос!"
    )


@router.message(KnowledgeStates.waiting_text)
async def knowledge_wrong_type(message: Message) -> None:
    await message.answer("✋ Пожалуйста, отправьте текст сообщением.")


@router.message(F.text == "📚 База знаний")
async def reply_kb_knowledge(message: Message, user: User) -> None:

    await message.answer(
        "📚 <b>База знаний</b>\n\nЗагрузите FAQ, цены, условия — бот будет отвечать клиентам по этим данным.",
        reply_markup=knowledge_kb(user.plan != "free"),
    )


@router.message(F.text == "⭐️ Тарифы")
async def reply_kb_plans(
    message: Message, catalog, state: FSMContext = None
) -> None:
    from app.bot.handlers.payments import cmd_buy

    await cmd_buy(message, catalog, state)


@router.message(F.text == "💬 Задать вопрос")
async def reply_kb_hint(message: Message) -> None:
    await message.answer("Просто напишите ваш вопрос следующим сообщением — я отвечу 🙂")