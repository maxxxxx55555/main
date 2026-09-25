"""/buy, pre_checkout_query, successful_payment — Telegram Stars (§5)."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.helpers import safe_edit, send_authored
from app.bot.keyboards.inline import plans_kb
from app.config import Settings
from app.db.models.user import User
from app.services.billing.plans import PlanCatalog
from app.services.billing.stars import StarsBillingService

router = Router(name="payments")
logger = logging.getLogger(__name__)

PAYMENT_MISMATCH = (
    "⚠️ Оплата получена, но платёж не привязался к этому аккаунту.\n"
    "Напишите в поддержку — мы активируем тариф вручную."
)


def _plans_text(catalog: PlanCatalog) -> str:
    lines = [
        "⭐️ <b>Тарифы</b>",
        "",
        *(
            f"• <b>{p.title}</b> — {p.price_stars} Stars: {p.description}"
            for p in catalog.paid()
        ),
        "",
        (
            "Оплата — Telegram Stars: в 2 клика, без карты. Продление того же "
            "тарифа добавляет новый период к текущему."
        ),
        "Выберите тариф:",
    ]
    return "\n".join(lines)


@router.message(Command("buy"))
@router.callback_query(F.data == "plans")
async def cmd_buy(event: Message | CallbackQuery, catalog: PlanCatalog, state: FSMContext) -> None:
    await state.clear()
    text = _plans_text(catalog)
    if isinstance(event, CallbackQuery):
        await safe_edit(event.message, text, reply_markup=plans_kb(catalog))
        await event.answer()
    else:
        await send_authored(event, text, reply_markup=plans_kb(catalog))


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(
    callback: CallbackQuery,
    user: User,
    catalog: PlanCatalog,
    billing: StarsBillingService,
) -> None:
    plan_id = callback.data.split(":", 1)[1]
    plan = catalog.get(plan_id)
    if plan is None or plan.price_stars <= 0 or callback.message is None:
        await callback.answer("Тариф недоступен", show_alert=True)
        return
    title = f"Тариф {plan.title}" + (" (продление)" if user.plan == plan.id else "")
    await callback.message.answer_invoice(
        title=title[:32],
        description=f"{plan.message_limit} сообщений AI-Сотрудника + база знаний",
        payload=billing.build_payload(plan.id, user.tg_id),
        currency="XTR",
        prices=[LabeledPrice(label=plan.title, amount=plan.price_stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, billing: StarsBillingService) -> None:
    """Лёгкая валидация против каталога (§5.2.2): без БД и внешних вызовов."""
    intent = billing.validate_payload(query.invoice_payload, query.total_amount)
    if intent is None:
        await query.answer(ok=False, error_message="Тариф или цена недействительны. Попробуйте /buy ещё раз.")
        return
    if query.currency != "XTR" or not billing.is_valid_payer(intent, query.from_user.id):
        logger.warning(
            "pre_checkout отклонён: currency=%s payer=%s payload_user=%s",
            query.currency,
            query.from_user.id,
            intent.user_tg_id,
        )
        await query.answer(ok=False, error_message="Платёж не соответствует счёту. Попробуйте /buy ещё раз.")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    user: User,
    session: AsyncSession,
    billing: StarsBillingService,
    settings: Settings,
) -> None:
    payment: SuccessfulPayment = message.successful_payment
    intent = billing.validate_payload(payment.invoice_payload, payment.total_amount)
    if intent is None:
        logger.error("Invalid payload at successful_payment: %r", payment.invoice_payload)
        await message.answer("Оплата получена, но возникла ошибка активации. Мы свяжемся с вами.")
        return

    payer_id = message.from_user.id if message.from_user else None
    if payer_id is None or not billing.is_valid_payer(intent, payer_id):
        logger.error(
            "Payment payer mismatch: payer=%s payload_user=%s charge=%s",
            payer_id,
            intent.user_tg_id,
            payment.telegram_payment_charge_id,
        )
        await message.answer(PAYMENT_MISMATCH)
        return

    plan = await billing.activate(
        session,
        user,
        intent.plan.id,
        payment.total_amount,
        payment.telegram_payment_charge_id,
    )
    if plan is None:
        # Дубликат доставки — план уже активирован ранее (идемпотентность §5.3)
        await message.answer("Этот платёж уже был активирован ранее ✅")
        return

    await session.refresh(user)
    reset = user.period_reset_at.strftime("%d.%m.%Y")
    logger.info(
        "Тариф активирован: user_id=%s plan=%s stars=%s",
        user.id,
        plan.id,
        payment.total_amount,
    )
    await send_authored(
        message,
        f"🎉 Тариф <b>{plan.title}</b> активирован!\n"
        f"Лимит: {plan.message_limit} сообщений до {reset}.\n\n"
        "База знаний доступна в разделе /knowledge — я начну отвечать "
        "от лица вашего бизнеса. Задайте тестовый вопрос клиента!",
    )