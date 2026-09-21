"""Каталог тарифов — единственный источник истины по лимитам и ценам (§4.1)."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


@dataclass(frozen=True)
class Plan:
    id: str
    title: str
    price_stars: int  # 0 — бесплатный
    message_limit: int  # сообщений за период
    description: str


class PlanCatalog:
    def __init__(self, settings: Settings) -> None:
        self._plans: dict[str, Plan] = {
            "free": Plan(
                id="free",
                title="Free",
                price_stars=0,
                message_limit=settings.free_limit,
                description="Базовый чат с AI-ассистентом",
            ),
            "pro": Plan(
                id="pro",
                title="Pro",
                price_stars=settings.pro_price_stars,
                message_limit=settings.pro_limit,
                description="500 сообщений + база знаний (RAG)",
            ),
            "business": Plan(
                id="business",
                title="Business",
                price_stars=settings.business_price_stars,
                message_limit=settings.business_limit,
                description="2000 сообщений + RAG + приоритетная очередь",
            ),
        }

    def get(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def paid(self) -> list[Plan]:
        return [p for p in self._plans.values() if p.price_stars > 0]

    def all(self) -> list[Plan]:
        return list(self._plans.values())

    def limit_for(self, plan_id: str) -> int:
        plan = self._plans.get(plan_id)
        return plan.message_limit if plan else self._plans["free"].message_limit
