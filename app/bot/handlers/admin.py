"""/adminstats, /broadcast, /refund — только для ADMIN_IDS (§9.5).

Выручка считается только по платежам со статусом paid (возвраты не в счёте).
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.message import Message as MessageModel
from app.db.models.payment import Payment
from app.db.models.user import User
from app.db.repo.payments import PaymentRepo
from app.db.repo.users import UserRepo
from app.services.billing.stars import StarsBillingService

router = Router(name="admin")
logger = logging.getLogger(__name__)

FORBIDDEN = "⛔️ Команда недоступна."
BROADCAST_DELAY_S = 0.05  # ~20 сообщений/сек — безопасно для лимитов Telegram
BROADCAST_MAX_LEN = 3000


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_id_set


@router.message(Command("adminstats"))
async def admin_stats(message: Message, session: AsyncSession, settings: Settings) -> None:
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
    breakdown = " · ".join(f"{plan}: {count}" for plan, count in plan_rows) or "—"

    await message.answer(
        "📈 <b>Админ-статистика</b>\n"
        f"Пользователей: {users_total}\n"
        f"С оплатой: {paid_users}\n"
        f"Сообщений всего: {messages_total}\n"
        f"Выручка (Stars): {revenue} ⭐️\n"
        f"Возвраты: {refunded} ⭐️\n"
        f"Тарифы: {breakdown}"
    )


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
        await message.answer("Использование: /broadcast &lt;текст сообщения&gt;")
        return
    if len(text) > BROADCAST_MAX_LEN:
        await message.answer(f"✋ Максимум {BROADCAST_MAX_LEN} символов.")
        return

    tg_ids = list((await session.execute(select(User.tg_id))).scalars().all())
    await message.answer(f"📣 Рассылаю {len(tg_ids)} пользователям…")
    sent = failed = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(tg_id, text, parse_mode=None)
            sent += 1
        except Exception:  # noqa: BLE001 — заблокировали/удалили: не прерываем рассылку
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