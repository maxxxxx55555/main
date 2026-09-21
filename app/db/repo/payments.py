from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.payment import Payment
from app.db.repo.base import BaseRepo


class PaymentRepo(BaseRepo[Payment]):
    model = Payment

    async def create_paid_idempotent(
        self, user_id: int, plan: str, amount_stars: int, charge_id: str
    ) -> bool:
        """Идемпотентная запись платежа (§5.3).

        True — платёж записан (первичная доставка successful_payment).
        False — дубликат по telegram_payment_charge_id (повтор не активирует план).
        """
        exists = await self.session.scalar(
            select(Payment.id).where(Payment.telegram_payment_charge_id == charge_id)
        )
        if exists is not None:
            return False

        values = dict(
            user_id=user_id,
            plan=plan,
            amount_stars=amount_stars,
            status="paid",
            telegram_payment_charge_id=charge_id,
        )
        dialect = getattr(getattr(self.session, "bind", None), "dialect", None)
        if dialect is not None and dialect.name == "postgresql":
            stmt = pg_insert(Payment).values(**values).on_conflict_do_nothing(
                index_elements=["telegram_payment_charge_id"]
            )
        else:
            stmt = sqlite_insert(Payment).values(**values).on_conflict_do_nothing(
                index_elements=["telegram_payment_charge_id"]
            )
        await self.session.execute(stmt)
        await self.session.flush()
        return True

    async def mark_refunded(self, charge_id: str) -> Payment | None:
        payment = await self.session.scalar(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )
        if payment is None or payment.status != "paid":
            return None
        payment.status = "refunded"
        await self.session.flush()
        return payment

    async def get_by_charge_id(self, charge_id: str) -> Payment | None:
        return await self.session.scalar(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )