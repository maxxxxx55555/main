"""Основной диалог с LLM: лимиты → контекст (+RAG) → провайдер → ответ."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import upsell_kb
from app.config import Settings
from app.db.models.user import User
from app.db.repo.messages import MessageRepo
from app.db.repo.knowledge import KnowledgeRepo
from app.services.ai.context import build_context
from app.services.ai.provider import AIProvider, LLMUnavailable
from app.services.ai.prompt import build_system_prompt
from app.services.ai.rag import RagService
from app.services.billing.plans import PlanCatalog
from app.services.limits.usage import LimitExceeded, UsageService

router = Router(name="chat")
logger = logging.getLogger(__name__)

LLM_DOWN = (
    "😔 Сервис AI временно недоступен, попробуйте через несколько минут.\n"
    "Ваш лимит не списан."
)


@router.message(F.text, StateFilter(None))
async def handle_chat(
    message: Message,
    state: FSMContext,
    user: User,
    session: AsyncSession,
    provider: AIProvider,
    usage: UsageService,
    rag: RagService,
    catalog: PlanCatalog,
    settings: Settings,
) -> None:
    assert message.text is not None
    text = message.text

    if len(text) > settings.max_message_len:
        await message.answer(
            f"✋ Сообщение слишком длинное (максимум {settings.max_message_len} символов). "
            "Разбейте его на части."
        )
        return

    # 1) Атомарное списание (§4.2); при отказе LLM — возврат (§8.3)
    try:
        remaining = await usage.consume(session, user)
    except LimitExceeded as exc:
        await message.answer(
            "🚧 Лимит сообщений на текущий период исчерпан.\n"
            f"Лимит обновится {exc.reset_at.strftime('%d.%m.%Y')}.",
            reply_markup=upsell_kb(catalog),
        )
        return

    # 2) Сохраняем сообщение пользователя
    await MessageRepo(session).add_message(user.id, "user", text)

    # 3) Контекст + RAG (только платные тарифы)
    knowledge_text = None
    if user.plan != "free":
        chunks = await rag.retrieve(session, user.id, text)
        if chunks:
            knowledge_text = "\n---\n".join(chunks)

    history_rows = await MessageRepo(session).recent(user.id, settings.context_window)
    history = [(row.role, row.content) for row in history_rows]
    llm_messages = build_context(
        build_system_prompt(knowledge_text, user.tz),
        history[:-1],  # текущее сообщение добавляем отдельно последним
        settings.context_window,
        settings.context_token_budget,
    )
    if not llm_messages or llm_messages[-1].get("content") != text:
        llm_messages.append({"role": "user", "content": text})

    # 4) Вызов LLM с graceful degradation
    try:
        reply = await provider.chat(llm_messages)
    except LLMUnavailable:
        logger.error("LLM unavailable for user_id=%s; usage refunded", user.id)
        await usage.refund(session, user)
        await message.answer(LLM_DOWN)
        return

    # 5) Сохраняем ответ + мягкие уведомления 80/100% (§4.4)
    await MessageRepo(session).add_message(user.id, "assistant", reply.content, reply.tokens)
    limit = catalog.limit_for(user.plan)
    suffix = usage.warning_suffix(remaining, limit, user.period_reset_at)
    await message.answer(reply.content[:4096 - len(suffix)] + suffix)