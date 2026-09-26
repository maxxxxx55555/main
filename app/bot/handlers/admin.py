"""/adminstats (enhanced), /adminleads, /adminpersona, /broadcast, /refund — только для ADMIN_IDS.

Выручка считается только по платежам со статусом paid (возвраты не в счёте).
Premium features: revenue analytics, lead capture management, AI personas, feedback stats.
"""

from __future__ import annotations

import asyncio
import csv
import datetime as dt
import io
import logging

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.lead import Feedback, Lead
from app.db.models.message import Message as MessageModel
from app.db.models.payment import Payment
from app.db.models.user import User
from app.db.repo.leads import LeadRepo
from app.db.repo.payments import PaymentRepo
from app.db.repo.users import UserRepo
from app.services.ai.personas import Persona
from app.services.billing.stars import StarsBillingService

router = Router(name="admin")
logger = logging.getLogger(__name__)

FORBIDDEN = "⛔️ Команда недоступна."
BROADCAST_DELAY_S = 0.05  # ~20 сообщений/сек — безопасно для лимитов Telegram
BROADCAST_MAX_LEN = 3000


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_id_set


@router.message(Command("adminstats"))
async def admin_stats(
    message: Message, session: AsyncSession, settings: Settings
) -> None:
    if not _is_admin(message, settings):
        await message.answer(FORBIDDEN)
        return

    users_total = (await session.execute(select(func.count(User.id)))).scalar_one()
    paid_users = (
        await session.execute(select(func.count(func.distinct(Payment.user_id))))
    ).scalar_one()
    messages_total = (await session.execute(select(func.count(MessageModel.id)))).scalar_one()
    revenue = (
        await session.execute(
            select(func.sum(Payment.amount_stars)).where(Payment.status == "paid")
        )
    ).scalar() or 0
    refunded = (
        await session.execute(
            select(func.sum(Payment.amount_stars)).where(Payment.status == "refunded")
        )
    ).scalar() or 0
    plan_rows = (
        await session.execute(select(User.plan, func.count(User.id)).group_by(User.plan))
    ).all()

    rev_by_plan = (
        await session.execute(
            select(Payment.plan, func.sum(Payment.amount_stars).label("total"))
            .where(Payment.status == "paid")
            .group_by(Payment.plan)
        )
    ).all()
    rev_breakdown = " · ".join(f"{row.plan}: {row.total}⭐" for row in rev_by_plan) or "—"

    week_ago = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    active_week = (
        await session.execute(
            select(func.count(func.distinct(User.id)))
            .where(User.created_at >= week_ago)
        )
    ).scalar_one()

    leads_stats = await LeadRepo(session).stats()
    feedback_count = (await session.execute(select(func.count(Feedback.id)))).scalar_one()
    avg_rating = (
        await session.execute(select(func.avg(Feedback.rating)))
    ).scalar() or 0

    breakdown = " · ".join(f"{plan}: {count}" for plan, count in plan_rows) or "—"

    await message.answer(
        "📊 <b>Продвинутая статистика премиум-сервиса</b>\n"
        f"👥 Пользователей: {users_total} (активных за неделю: {active_week})\n"
        f"💎 С оплатой: {paid_users}\n"
        f"💬 Сообщений всего: {messages_total}\n\n"
        f"💰 Выручка: {revenue} ⭐️\n"
        f"↩️  Возвраты: {refunded} ⭐️\n"
        f"📈 Выручка по тарифам:\n  {rev_breakdown}\n\n"
        f"📋 Тарифы: {breakdown}\n\n"
        f"🎯 Лиды: {leads_stats['total']} (скор: {leads_stats['avg_score']:.0f}/100)\n"
        f"⭐ Отзывов: {feedback_count} (оценка: {avg_rating:.1f}/5)\n\n"
        f"🚀 /adminleads · /adminpersona · /broadcast",
    )


@router.message(Command("adminleads"))
async def admin_leads(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    settings: Settings,
) -> None:
    """Управление лидами: /adminleads list | export | detail <id> | reset <id>"""
    if not _is_admin(message, settings):
        await message.answer(FORBIDDEN)
        return

    action = (command.args or "").strip().split()
    action_cmd = action[0].lower() if action else "list"
    repo = LeadRepo(session)

    if action_cmd == "export":
        leads = await repo.recent(limit=1000)
        if not leads:
            await message.answer("📥 Лидов пока нет для экспорта.")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "User TG ID", "Name", "Contact", "Interest", "Score", "Source", "Captured At", "Notes"])
        for lead in leads:
            writer.writerow([lead.id, lead.user_id, lead.name or "", lead.contact or "",
                            lead.interest, lead.score, lead.source,
                            lead.captured_at.strftime("%Y-%m-%d %H:%M"), lead.notes])
        await message.answer_document(
            BufferedInputFile(output.getvalue().encode("utf-8"), filename=f"leads_{dt.date.today()}.csv"),
            caption=f"📥 {len(leads)} лидов экспортировано",
        )
    elif action_cmd == "detail" and len(action) > 1:
        lead = await session.get(Lead, int(action[1]))
        if lead is None:
            await message.answer("Лид не найден.")
            return
        await message.answer(
            f"🎯 <b>Лид #{lead.id}</b>\n"
            f"👤 Имя: {lead.name or '—'}\n"
            f"📞 Контакт: {lead.contact or '—'}\n"
            f"💼 Интерес: {lead.interest}\n"
            f"⭐ Оценка: {lead.score}/100\n"
            f"📊 Источник: {lead.source}\n"
            f"🕒 Пойман: {lead.captured_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📝 Примечание: {lead.notes[:200] if lead.notes else '—'}",
        )
    elif action_cmd == "reset" and len(action) > 1:
        lead = await session.get(Lead, int(action[1]))
        if lead is None:
            await message.answer("Лид не найден.")
            return
        lead.score = 50
        lead.notes = ""
        await session.commit()
        await message.answer(f"🔄 Лид #{lead.id} сброшен.")
    else:
        leads = await repo.recent(limit=20)
        if not leads:
            await message.answer("🎯 Пока нет захваченных лидов.")
            return
        lines = [f"#{l.id} | {l.name or 'anon'} | {l.interest} | ⭐{l.score} | {l.captured_at.strftime('%d.%m %H:%M')}" for l in leads]
        await message.answer(
            f"🎯 <b>Последние {len(leads)} лидов</b>:\n\n" + "\n".join(lines)
            + "\n\nЭкспорт: /adminleads export | Детали: /adminleads detail <id> | Сброс: /adminleads reset <id>",
        )


@router.message(Command("adminpersona"))
async def admin_persona(
    message: Message,
    command: CommandObject,
    settings: Settings,
) -> None:
    """AI-персоны: /adminpersona list | set <key>"""
    if not _is_admin(message, settings):
        await message.answer(FORBIDDEN)
        return

    action = (command.args or "").strip().split()
    action_cmd = action[0].lower() if action else "list"
    available_keys = {p.key for p in Persona}

    if action_cmd == "list":
        lines = [f"<code>{p.key}</code> — {p.title}" for p in Persona]
        current = getattr(settings, "_ai_persona_override", "auto")
        await message.answer(
            "🎭 <b>Доступные AI-персоны</b>:\n\n" + "\n".join(lines)
            + f"\n\nТекущая: {current}\nПрименить: /adminpersona set <key>",
        )
    elif action_cmd == "set" and len(action) > 1:
        key = action[1].lower()
        if key not in available_keys:
            await message.answer(f"❌ Неизвестная персона: {key}. /adminpersona list")
            return
        settings._ai_persona_override = key  # type: ignore[attr-defined]
        await message.answer(f"✅ Персона установлена: {Persona.by_key(key).title}")
    else:
        await message.answer("Использование: /adminpersona list | set <key>")


@router.message(Command("broadcast"))
async def admin_broadcast(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
    settings: Settings,
) -> None:
    """Рассылка всем пользователям: /broadcast <текст> (plain text, без разметки)."""
    if not _is_admin(message, settings):
        await message.answer(FORBIDDEN)
        return
    text = (command.args or "").strip()
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return
    if len(text) > BROADCAST_MAX_LEN:
        await message.answer(f"✋ Максимум {BROADCAST_MAX_LEN} символов.")
        return

    tg_ids = list((await session.execute(select(User.tg_id))).scalars().all())
    if not tg_ids:
        await message.answer("📣 Нечего рассылать: пользователей пока нет.")
        return
    await message.answer(f"📣 Рассылаю {len(tg_ids)} пользователям…")
    sent = failed = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(tg_id, text, parse_mode=None)
            sent += 1
        except Exception:  # noqa: BLE001
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY_S)
    logger.info("Broadcast: sent=%s failed=%s total=%s", sent, failed, len(tg_ids))
    await message.answer(f"✅ Готово: доставлено {sent}, недоступно {failed}.")


@router.message(Command("refund"))
async def admin_refund(
    message: Message,
    session: AsyncSession,
    billing: StarsBillingService,
    settings: Settings,
) -> None:
    """Использование: /refund <telegram_payment_charge_id>"""
    if not _is_admin(message, settings):
        await message.answer(FORBIDDEN)
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        await message.answer("Использование: /refund &lt;telegram_payment_charge_id&gt;")
        return
    charge_id = parts[1].strip()

    payment_record = await PaymentRepo(session).get_by_charge_id(charge_id)
    if payment_record is None:
        await message.answer("Платёж не найден.")
        return
    user = await UserRepo(session).get(payment_record.user_id)
    if user is None:
        await message.answer("Пользователь не найден.")
        return
    if message.bot is None:
        await message.answer("❌ Нет доступа к Bot API.")
        return
    try:
        await message.bot.refund_star_payment(
            user_id=user.tg_id, telegram_payment_charge_id=charge_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Refund API failed for %s: %s", charge_id, exc)
        await message.answer("❌ Telegram отклонил возврат (подробности в логах).")
        return
    ok = await billing.refund(session, user, charge_id)
    await message.answer("✅ Возврат выполнен, план переведён в Free." if ok else "⚠️ Возврат выполнен в Telegram, но запись уже не в статусе paid.")