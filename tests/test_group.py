"""Тесты группового чат-бота: модерация, анти-спам, рейтинги, приветствия."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models.chat import ChatMemberActivity, ChatSettings
from app.db.repo.chats import ActivityRepo, ChatRepo


# --- Model / Schema tests ---

def test_chat_settings_model_fields():
    """Модель ChatSettings имеет все нужные поля."""
    from app.db.models.chat import ChatSettings

    columns = {c.name for c in ChatSettings.__table__.columns}
    expected = {
        "chat_id", "title", "welcome_enabled", "welcome_message",
        "rules", "anti_spam_enabled", "delete_service_messages",
        "warn_threshold", "mute_duration_min", "auto_moderate",
        "created_at", "updated_at",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_chat_activity_model_fields():
    """Модель ChatMemberActivity имеет все нужные поля."""
    from app.db.models.chat import ChatMemberActivity

    columns = {c.name for c in ChatMemberActivity.__table__.columns}
    expected = {
        "id", "chat_id", "user_id", "username", "first_name",
        "message_count", "score", "last_active",
    }
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


# --- Repo tests ---

@pytest.fixture
def chat_id() -> int:
    return -1001234567890  # супергруппа


async def test_chat_repo_get_or_create(engine, chat_id):
    """ChatRepo.get_or_create создаёт и возвращает настройки чата."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        repo = ChatRepo(db)
        settings = await repo.get_or_create(chat_id, "Test Group")
        assert settings.chat_id == chat_id
        assert settings.title == "Test Group"
        assert settings.welcome_enabled is True
        assert settings.anti_spam_enabled is True

        settings2 = await repo.get_or_create(chat_id, "Updated Title")
        assert settings2.chat_id == chat_id
        assert settings2.title == "Updated Title"


async def test_chat_repo_update_rules(engine, chat_id):
    """ChatRepo.update_rules сохраняет правила чата."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        repo = ChatRepo(db)
        settings = await repo.update_rules(chat_id, "1. Не спамить\n2. Уважать участников")
        assert "Не спамить" in settings.rules

        settings2 = await repo.get(chat_id)
        assert settings2 is not None
        assert "Не спамить" in settings2.rules


async def test_chat_repo_update_welcome(engine, chat_id):
    """ChatRepo.update_welcome сохраняет кастомное приветствие."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        repo = ChatRepo(db)
        settings = await repo.update_welcome(
            chat_id, "Привет, {name}! Добро пожаловать.", enabled=True
        )
        assert settings.welcome_enabled is True
        assert "{name}" in settings.welcome_message

        settings2 = await repo.update_welcome(chat_id, "", enabled=False)
        assert settings2.welcome_enabled is False


async def test_chat_repo_toggle_anti_spam(engine, chat_id):
    """ChatRepo.toggle_anti_spam включает/выключает анти-спам."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        repo = ChatRepo(db)
        settings = await repo.toggle_anti_spam(chat_id, False)
        assert settings.anti_spam_enabled is False

        settings2 = await repo.toggle_anti_spam(chat_id, True)
        assert settings2.anti_spam_enabled is True


async def test_activity_repo_reset_activity(engine, chat_id):
    """ActivityRepo.reset_activity сбрасывает все счётчики."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        await ChatRepo(db).get_or_create(chat_id, "Test")
        repo = ActivityRepo(db)
        await repo.add_message(chat_id, 1, "alice", "Alice")

        await repo.reset_activity(chat_id)

        result = (
            await db.execute(
                select(func.sum(ChatMemberActivity.message_count)).where(
                    ChatMemberActivity.chat_id == chat_id
                )
            )
        ).scalar() or 0
        assert result == 0


# --- Text tests ---

def test_not_admin_text_exists():
    """Текст для не-админа существует."""
    from app.bot import texts
    assert texts.NOT_ADMIN
    assert "администратор" in texts.NOT_ADMIN.lower()


def test_default_welcome_group_has_placeholders():
    """Шаблон приветствия содержит placeholder для имени."""
    from app.bot import texts
    assert "{name}" in texts.DEFAULT_WELCOME_GROUP


def test_chat_stats_text():
    """chat_stats() формирует корректный текст."""
    from app.bot import texts
    stats = {"total_messages": 150, "active_users": 25, "active_week": 18}
    body = texts.chat_stats(stats)
    assert "150" in body
    assert "25" in body
    assert "18" in body
    assert "/top" in body


# --- Handler registration tests ---

def test_mute_command_registered():
    """Команда /mute зарегистрирована в роутере группы."""
    from app.bot.handlers.group import router
    # Collect command names from all message handlers' filters
    cmd_names: set[str] = set()
    for h in router.message.handlers:  # type: ignore
        for f in h.filters or []:
            # Command filters store commands in f.callback.commands
            if hasattr(f, "callback") and hasattr(f.callback, "commands"):
                cmd_names.update(f.callback.commands)
            # MagicFilter stores its spec in f.magic
            elif hasattr(f, "magic") and f.magic is not None:
                cmd_names.add(str(f.magic))
    assert "mute" in cmd_names


def test_top_command_registered():
    """Команда /top зарегистрирована в роутере группы."""
    from app.bot.handlers.group import router
    cmd_names: set[str] = set()
    for h in router.message.handlers:  # type: ignore
        for f in h.filters or []:
            if hasattr(f, "callback") and hasattr(f.callback, "commands"):
                cmd_names.update(f.callback.commands)
    assert "top" in cmd_names


def test_persona_in_prompt_for_group():
    """AI-персоны корректно встраиваются в системный промпт."""
    from app.services.ai.personas import Persona, PERSONA_PROMPTS
    from app.services.ai.prompt import build_system_prompt
    for persona in Persona:
        prompt = build_system_prompt(knowledge=None, tz="UTC", persona=persona.key)
        assert "AI-Сотрудник" in prompt


async def test_activity_repo_add_message(engine, chat_id):
    """ActivityRepo.add_message создаёт и увеличивает счётчики."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        await ChatRepo(db).get_or_create(chat_id, "Test")

        repo = ActivityRepo(db)
        await repo.add_message(chat_id, 12345, "alice", "Alice")
        await repo.add_message(chat_id, 12345, "alice", "Alice")
        await repo.add_message(chat_id, 67890, "bob", "Bob")

        top = await repo.top_users(chat_id, limit=10)
        assert len(top) == 2
        assert top[0].user_id == 12345
        assert top[0].message_count == 2
        assert top[0].score == 2
        assert top[1].user_id == 67890


async def test_activity_repo_chat_stats(engine, chat_id):
    """ActivityRepo.chat_stats возвращает агрегированную статистику."""
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        await ChatRepo(db).get_or_create(chat_id, "Test")
        repo = ActivityRepo(db)
        await repo.add_message(chat_id, 1, "alice", "Alice")
        await repo.add_message(chat_id, 2, "bob", "Bob")
        await repo.add_message(chat_id, 1, "alice", "Alice")

        stats = await repo.chat_stats(chat_id)
        assert stats["total_messages"] == 3
        assert stats["active_users"] == 2
        assert stats["active_week"] == 2
