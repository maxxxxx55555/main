"""Каталог тарифов и валидация payload Telegram Stars (§4.1, §5)."""

from __future__ import annotations

from app.db.repo.users import UserRepo
from app.services.billing.plans import PlanCatalog
from app.services.billing.stars import StarsBillingService


def test_catalog_values(settings):
    catalog = PlanCatalog(settings)
    assert catalog.get("free").price_stars == 0
    assert catalog.get("pro").price_stars == 100
    assert catalog.get("business").price_stars == 250
    assert catalog.limit_for("free") == 2
    assert catalog.limit_for("pro") == 5
    assert catalog.limit_for("unknown") == 2  # fallback free
    assert [p.id for p in catalog.paid()] == ["pro", "business"]


def test_validate_payload_ok(settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    intent = billing.validate_payload("buy:pro:12345", 100)
    assert intent is not None
    assert intent.plan.id == "pro"
    assert intent.user_tg_id == 12345


def test_validate_payload_wrong_price(settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    # Подделка: цена не из каталога
    assert billing.validate_payload("buy:pro:12345", 50) is None


def test_validate_payload_unknown_plan(settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    assert billing.validate_payload("buy:enterprise:12345", 100) is None
    assert billing.validate_payload("buy:free:12345", 0) is None  # free не продаётся


def test_validate_payload_malformed(settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    assert billing.validate_payload("garbage", 100) is None
    assert billing.validate_payload("buy:pro:notanumber", 100) is None


def test_is_valid_payer_blocks_foreign_invoice(settings):
    """Инвойс, выпущенный для другого пользователя, оплатить нельзя (§5.2.2)."""
    billing = StarsBillingService(PlanCatalog(settings), settings)
    intent = billing.validate_payload("buy:pro:12345", 100)
    assert intent is not None
    assert billing.is_valid_payer(intent, 12345) is True
    assert billing.is_valid_payer(intent, 99999) is False


async def test_activate_is_idempotent(session, settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    user = await UserRepo(session).get_or_create(1)

    plan = await billing.activate(session, user, "pro", 100, "charge-1")
    assert plan is not None and plan.id == "pro"
    assert user.plan == "pro"
    assert user.messages_used == 0

    # Повторная доставка того же платежа — дубликат НЕ активирует повторно
    dup = await billing.activate(session, user, "pro", 100, "charge-1")
    assert dup is None


async def test_activate_extends_same_plan(session, settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    repo = UserRepo(session)
    user = await repo.get_or_create(2)
    first = await billing.activate(session, user, "pro", 100, "c-1")
    first_reset = user.period_reset_at
    second = await billing.activate(session, user, "pro", 100, "c-2")
    assert first is not None and second is not None
    assert user.period_reset_at > first_reset  # продление: max(now, reset) + 30d


async def test_activate_upgrade_resets_usage(session, settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    user = await UserRepo(session).get_or_create(3)
    user.messages_used = 2
    await billing.activate(session, user, "business", 250, "c-3")
    assert user.plan == "business"
    assert user.messages_used == 0


async def test_refund_downgrades(session, settings):
    billing = StarsBillingService(PlanCatalog(settings), settings)
    user = await UserRepo(session).get_or_create(4)
    await billing.activate(session, user, "pro", 100, "c-4")
    assert user.plan == "pro"

    ok = await billing.refund(session, user, "c-4")
    assert ok is True
    assert user.plan == "free"

    # Повторный refund по тому же charge_id невозможен
    assert await billing.refund(session, user, "c-4") is False