from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

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

        Реализация — ON CONFLICT DO NOTHING: гонка двух параллельных доставок
        одного charge_id атомарно разрешается на уровне БД, а не check-then-insert
        (SELECT перед INSERT пропускал бы дубли under concurrency).
        """
        values = {
            "user_id": user_id,
            "plan": plan,
            "amount_stars": amount_stars,
            "status": "paid",
            "telegram_payment_charge_id": charge_id,
        }
        dialect = getattr(getattr(self.session, "bind", None), "dialect", None)
        if dialect is not None and dialect.name == "postgresql":
            stmt = pg_insert(Payment).values(**values).on_conflict_do_nothing(
                index_elements=["telegram_payment_charge_id"]
            )
        else:
            stmt = sqlite_insert(Payment).values(**values).on_conflict_do_nothing(
                index_elements=["telegram_payment_charge_id"]
            )
        result = await self.session.execute(stmt)
        await self.session.flush()
        # rowcount==1 — вставка прошла; 0 — конфликт по UNIQUE (дубликат доставки).
        return (result.rowcount or 0) == 1

    async def mark_refunded(self, charge_id: str) -> Payment | None:
        payment = await self.session.scalar(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )
        if payment is None or payment.status != "paid":
            return None
        payment.status = "refunded"
        await self.session.flush()
        return payment

    async def delete_for_user(self, user_id: int) -> int:
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(Payment).where(Payment.user_id == user_id)
        )
        return result.rowcount or 0

    async def get_by_charge_id(self, charge_id: str) -> Payment | None:
        return await self.session.scalar(
            select(Payment).where(Payment.telegram_payment_charge_id == charge_id)
        )