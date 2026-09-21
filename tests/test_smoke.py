"""Smoke: приложение собирается целиком — роутеры, сервисы, фабрика провайдера."""

from __future__ import annotations


def test_app_assembles(settings):
    from app.bot.router import build_router
    from app.config import Settings, get_settings
    from app.db.base import build_engine, build_sessionmaker
    from app.main import run  # noqa: F401 — импорт точки входа валиден
    from app.services.ai.provider import MockProvider, build_provider
    from app.services.ai.rag import RagService
    from app.services.billing.plans import PlanCatalog
    from app.services.billing.stars import StarsBillingService
    from app.services.limits.usage import UsageService

    catalog = PlanCatalog(settings)
    usage = UsageService(catalog, settings.period_days)
    billing = StarsBillingService(catalog, settings)
    rag = RagService(build_provider(settings), settings)

    router = build_router()
    assert len(router.sub_routers) == 5  # payments, admin, start, knowledge, chat

    # Инварианты каталога (§4.1)
    assert catalog.get("free").price_stars == 0
    assert all(p.price_stars > 0 for p in catalog.paid())
    assert usage.catalog is catalog and billing.catalog is catalog
    assert isinstance(rag.provider, MockProvider)  # без ключа — mock (§6.1)


def test_settings_env_parsing():
    from app.config import Settings

    s = Settings(admin_ids="111, 222,333", llm_api_key="")
    assert s.admin_id_set == {111, 222, 333}
    assert s.use_mock_llm is True
    s2 = Settings(admin_ids="", llm_api_key="sk-x")
    assert s2.admin_id_set == set()
    assert s2.use_mock_llm is False


def test_get_settings_cached():
    from app.config import get_settings

    assert get_settings() is get_settings()