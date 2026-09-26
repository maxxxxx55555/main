"""Основной диалог с LLM: лимиты → контекст (+RAG) → провайдер → безопасный ответ."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.helpers import send_llm
from app.bot.keyboards.inline import upsell_kb
from app.config import Settings
from app.db.models.user import User
from app.db.repo.leads import LeadRepo
from app.db.repo.messages import MessageRepo
from app.services.ai.context import build_context
from app.services.ai.prompt import build_system_prompt
from app.services.ai.provider import AIProvider, LLMUnavailable
from app.services.ai.rag import RagService
from app.services.billing.plans import PlanCatalog
from app.services.limits.usage import LimitExceeded, UsageService

router = Router(name="chat")
logger = logging.getLogger(__name__)

EMPTY_REPLY = "🤔 Мне нечего добавить по этому запросу. Попробуйте переформулировать вопрос."


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
    text = message.text.strip()

    if len(text) > settings.max_message_len:
        await message.answer(texts.message_too_long(settings.max_message_len))
        return

    # 1) Атомарное списание (§4.2); при отказе LLM — возврат (§8.3)
    try:
        remaining = await usage.consume(session, user)
    except LimitExceeded as exc:
        await message.answer(
            texts.limit_reached(exc.reset_at.strftime("%d.%m.%Y")),
            reply_markup=upsell_kb(),
        )
        return

    # 2) Сохраняем сообщение пользователя (оно же войдёт в контекст следующего запроса)
    repo = MessageRepo(session)
    await repo.add_message(user.id, "user", text)

        # 3) Контекст + RAG (база знаний — только на платных тарифах)
    knowledge_text = None
    if user.plan != "free":
        try:
            chunks = await rag.retrieve(session, user.id, text)
        except Exception:  # сбой базы знаний не должен ломать чат (§8.3)
            logger.exception("RAG retrieve failed for user_id=%s", user.id)
            chunks = []
        if chunks:
            knowledge_text = "\n---\n".join(chunks)

    # Persona: admin override > settings.ai_persona > "auto"
    persona = getattr(settings, "_ai_persona_override", None) or settings.ai_persona
    history_rows = await repo.recent(user.id, settings.context_window)
    history = [(row.role, row.content) for row in history_rows]
    llm_messages = build_context(
        build_system_prompt(knowledge_text, user.tz, persona),
        history[:-1],  # текущее сообщение добавляем отдельно последним
        settings.context_window,
        settings.context_token_budget,
    )
    if not llm_messages or llm_messages[-1].get("content") != text:
        llm_messages.append({"role": "user", "content": text})

    # 4) Вызов LLM: «печатает…» + graceful degradation (лимит не списывается при сбое)
    try:
        async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
            reply = await provider.chat(llm_messages)
    except LLMUnavailable as exc:
        logger.error("LLM unavailable for user_id=%s: %s; usage refunded", user.id, exc)
        await usage.refund(session, user)
        await message.answer(texts.LLM_DOWN)
        return
    except Exception:  # любой сбой провайдера: возврат лимита + понятный ответ
        logger.exception("Unexpected LLM error for user_id=%s; usage refunded", user.id)
        await usage.refund(session, user)
        await message.answer(texts.LLM_DOWN)
        return

    # 5) Сохраняем ответ + мягкие уведомления 80/100% (§4.4)
    content = (reply.content or "").strip() or EMPTY_REPLY
    await repo.add_message(user.id, "assistant", content, reply.tokens)
    limit = catalog.limit_for(user.plan)
    suffix = usage.warning_suffix(remaining, limit, user.period_reset_at)
    # Upsell только free-пользователям: платным при лимите показываем /buy без PRO-CTA.
    markup = None
    if suffix:
        markup = upsell_kb() if user.plan == "free" else None

    # Premium: автоматический захват лидов из диалога
    try:
        await LeadRepo(session).capture(
            user_id=user.id,
            interest="Hot Lead" if "купить" in text.lower() or "заказ" in text.lower() else "General",
            score=85 if user.plan == "pro" else 60,
            notes=f"Q: {text[:100]}",
        )
        await session.commit()
    except Exception:  # Lead capture must never break the chat flow
        logger.exception("Lead capture failed for user_id=%s", user.id)

    await send_llm(message, content + suffix, reply_markup=markup)


@router.message(StateFilter(None))
async def not_a_text(message: Message) -> None:
    """Фолбэк для фото/голоса/стикеров: бот отвечает понятным текстом."""
    await message.answer(texts.NOT_TEXT)