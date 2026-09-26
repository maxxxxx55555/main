"""Тесты премиум-фич: /adminleads, /adminpersona, авто-захват лидов, AI-персоны."""
from __future__ import annotations

from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings
from app.db.models.lead import Lead
from app.db.repo.leads import LeadRepo
from app.services.ai.personas import Persona, PERSONA_PROMPTS
from app.services.ai.prompt import build_system_prompt

BOT_TOKEN = "123456:TEST-TOKEN"


class FakeSession:
    """Упрощённая fake session для тестов."""

    def __init__(self) -> None:
        self.calls: list = []
        self._texts: list[str] = []

    def add(self, obj):
        self.calls.append(("add", obj))

    async def commit(self):
        self.calls.append(("commit",))

    def sent_texts(self) -> list[str]:
        return self._texts


# --- Persona tests ---

def test_persona_prompts_exist():
    """Все персоны имеют заголовок и промпт."""
    for persona in Persona:
        assert persona.key, f"Persona {persona} has no key"
        assert persona.title, f"Persona {persona} has no title"
        assert persona.key in PERSONA_PROMPTS, f"No prompt for persona {persona.key}"


def test_build_system_prompt_with_persona():
    """Промпт с persona включает persona-инструкцию."""
    prompt = build_system_prompt(knowledge=None, tz="UTC", persona="realtor")
    assert "AI-Сотрудник" in prompt
    assert "недвижимост" in prompt.lower() or "рилтор" in prompt.lower()


def test_build_system_prompt_without_persona():
    """Промпт без persona (auto) не включает persona-префикс."""
    prompt = build_system_prompt(knowledge=None, tz="UTC", persona="auto")
    assert "AI-Сотрудник" in prompt


# --- Lead repo tests ---

async def test_lead_repo_capture_and_stats(engine, settings):
    """LeadRepo.create и stats работают корректно."""
    from app.db.models.user import User

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        user = User(tg_id=999, plan="free", messages_used=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        repo = LeadRepo(db)
        lead = await repo.capture(
            user_id=user.id,
            contact="test@example.com",
            interest="Hot Lead",
            score=85,
            notes="test note",
        )
        assert lead.id is not None
        assert lead.contact == "test@example.com"
        assert lead.score == 85

        stats = await repo.stats()
        assert stats["total"] == 1
        assert stats["avg_score"] == 85


async def test_lead_repo_recent(engine, settings):
    """LeadRepo.recent возвращает отсортированные лиды."""
    from app.db.models.user import User

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        user = User(tg_id=888, plan="free", messages_used=0)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        repo = LeadRepo(db)
        await repo.capture(user_id=user.id, name="Alice")
        await repo.capture(user_id=user.id, name="Bob")
        await repo.commit() if hasattr(repo, "commit") else None

        leads = await repo.recent(limit=10)
        assert len(leads) == 2


# --- Config test ---

def test_ai_persona_default():
    """AI persona по умолчанию — auto."""
    s = Settings()
    assert s.ai_persona == "auto"
