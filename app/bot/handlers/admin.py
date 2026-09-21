"""/adminstats, /refund — только для ADMIN_IDS (§9.5)."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.message import Message
from app.db.models.payment import Payment
from app.db.models.user import User
from app.db.repo.users import UserRepo
from app.services.billing.stars import StarsBillingService

router = Router(name="admin")
logger = logging.getLogger(__name__)


def _is_admin(message: Message, settings: Settings) -> bool:
    return message.from_user is not None and message.from_user.id in settings.admin_id_set


@router.message(Command("adminstats"))
async def admin_stats(message: Message, session: AsyncSession, settings: Settings) -> None:
    if not _is_admin(message, settings):
        return
    users_total = (await session.execute(select(func.count(User.id)))).scalar_one()
    paid_users = (
        await session.execute(select(func.count(func.distinct(Payment.user_id))))
    ).scalar_one()
    messages_total = (await session.execute(select(func.count(Message.id)))).scalar_one()
    revenue = (await session.execute(select(func.sum(Payment.amount_stars)))).scalar() or 0
    await message.answer(
        "📈 <b>Админ-статистика</b>\n"
        f"Пользователей: {users_total}\n"
        f"С оплатой: {paid_users}\n"
        f"Сообщений всего: {messages_total}\n"
        f"Выручка (Stars): {revenue} ⭐️"
    )


@router.message(Command("refund"))
async def admin_refund(
    message: Message,
    session: AsyncSession,
    billing: StarsBillingService,
    settings: Settings,
) -> None:
    """Использование: /refund <telegram_payment_charge_id>"""
    if not _is_admin(message, settings):
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /refund &lt;telegram_payment_charge_id&gt;")
        return
    charge_id = parts[1].strip()

    from app.db.repo.payments import PaymentRepo

    repo_payment = await PaymentRepo(session).get_by_charge_id(charge_id)
    if repo_payment is None:
        await message.answer("Платёж не найден.")
        return
    user = await UserRepo(session).get(repo_payment.user_id)
    if user is None:
        await message.answer("Пользователь не найден.")
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