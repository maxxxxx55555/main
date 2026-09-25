"""Telegram Stars (XTR): invoice, валидация pre_checkout, активация, refund (§5)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models.user import User
from app.db.repo.payments import PaymentRepo
from app.db.repo.users import UserRepo
from app.services.billing.plans import Plan, PlanCatalog

PAYLOAD_PREFIX = "buy"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InvoiceIntent:
    plan: Plan
    user_tg_id: int


class StarsBillingService:
    def __init__(self, catalog: PlanCatalog, settings: Settings) -> None:
        self.catalog = catalog
        self.settings = settings

    # --- 5.2.1 Invoice ---
    def build_payload(self, plan_id: str, user_tg_id: int) -> str:
        return f"{PAYLOAD_PREFIX}:{plan_id}:{user_tg_id}"

    # --- 5.2.2 pre_checkout: только лёгкая валидация, без БД ---
    def validate_payload(self, payload: str, amount_stars: int) -> InvoiceIntent | None:
        """Источник истины по цене — каталог, а не payload."""
        parts = payload.split(":")
        if len(parts) != 3 or parts[0] != PAYLOAD_PREFIX:
            return None
        plan = self.catalog.get(parts[1])
        if plan is None or plan.price_stars <= 0:
            return None
        if amount_stars != plan.price_stars:
            return None
        try:
            user_tg_id = int(parts[2])
        except ValueError:
            return None
        return InvoiceIntent(plan=plan, user_tg_id=user_tg_id)

    @staticmethod
    def is_valid_payer(intent: InvoiceIntent, payer_tg_id: int) -> bool:
        """Инвойс должен оплатить тот, для кого он выпущен (защита от подмены payload)."""
        return intent.user_tg_id == payer_tg_id

    # --- 5.2.3 successful_payment: единственная точка активации ---
    async def activate(
        self,
        session: AsyncSession,
        user: User,
        plan_id: str,
        amount_stars: int,
        telegram_payment_charge_id: str,
    ) -> Plan | None:
        """[tx] INSERT payments(paid) + UPDATE users(plan) — идемпотентно.

        Возвращает активированный тариф или None, если платёж-дубликат.
        """
        plan = self.catalog.get(plan_id)
        if plan is None or plan.price_stars <= 0:
            return None
        # Сумма из Telegram обязана совпадать с каталогом: источник цены — сервер,
        # а не payload. Без этого заниженный amount записал бы paid-строку за копейки.
        if amount_stars != plan.price_stars:
            logger.error(
                "Payment amount mismatch: plan=%s expected=%s got=%s",
                plan.id,
                plan.price_stars,
                amount_stars,
            )
            return None

        recorded = await PaymentRepo(session).create_paid_idempotent(
            user_id=user.id,
            plan=plan_id,
            amount_stars=amount_stars,
            charge_id=telegram_payment_charge_id,
        )
        if not recorded:
            return None  # дубликат — план не активируем повторно

        await UserRepo(session).set_plan(user, plan_id, self.settings.period_days)
        return plan

    # --- 5.3 Refund (инициирует бот, Telegram событие не присылает) ---
    async def refund(
        self, session: AsyncSession, user: User, telegram_payment_charge_id: str
    ) -> bool:
        """Статус → refunded; план → free (немедленная политика, §5.3)."""
        payment = await PaymentRepo(session).mark_refunded(telegram_payment_charge_id)
        if payment is None:
            return False
        await UserRepo(session).downgrade_to_free(user)
        return True
