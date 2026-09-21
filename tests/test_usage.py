"""Атомарное списание, ленивый сброс периода, refund usage (§4)."""

from __future__ import annotations

import datetime as dt

import pytest

from app.db.models.base import utcnow
from app.db.models.user import User
from app.db.repo.users import UserRepo
from app.services.billing.plans import PlanCatalog
from app.services.limits.usage import LimitExceeded, UsageService


async def _user(session) -> User:
    return await UserRepo(session).get_or_create(123, tz="UTC")


async def test_consume_increments_and_returns_remaining(session, settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    user = await _user(session)
    rem1 = await usage.consume(session, user)
    rem2 = await usage.consume(session, user)
    assert rem1 == 1  # free_limit=2
    assert rem2 == 0
    assert user.messages_used == 2


async def test_consume_raises_when_exhausted(session, settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    user = await _user(session)
    await usage.consume(session, user)
    await usage.consume(session, user)
    with pytest.raises(LimitExceeded):
        await usage.consume(session, user)


async def test_lazy_reset_after_period(session, settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    user = await _user(session)
    user.messages_used = 2
    user.period_reset_at = utcnow() - dt.timedelta(days=1)  # период истёк
    remaining = await usage.consume(session, user)
    assert remaining == 1  # счётчик сброшен, списание прошло
    assert user.messages_used == 1
    assert user.period_reset_at > utcnow()


async def test_no_reset_before_period_end(session, settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    user = await _user(session)
    user.messages_used = 2
    old_reset = user.period_reset_at
    with pytest.raises(LimitExceeded):
        await usage.consume(session, user)
    assert user.period_reset_at == old_reset  # сброса не было


async def test_refund_usage_on_llm_failure(session, settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    user = await _user(session)
    await usage.consume(session, user)
    await usage.refund(session, user)
    assert user.messages_used == 0


async def test_warning_suffix_thresholds(settings):
    usage = UsageService(PlanCatalog(settings), settings.period_days)
    reset = utcnow() + dt.timedelta(days=10)
    # Порог = max(limit // 5, 1): для лимита 30 — это 6
    assert usage.warning_suffix(7, 30, reset) == ""  # > 20% остатка
    assert "Осталось" in usage.warning_suffix(3, 30, reset)
    assert "Осталось" in usage.warning_suffix(1, 30, reset)
    assert "последнее" in usage.warning_suffix(0, 30, reset)