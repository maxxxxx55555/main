"""Меню команд, глобальный error-handler и защита платежа (bot/commands.py, bot/errors.py)."""

from __future__ import annotations

from datetime import UTC, datetime

from aiogram.types import Chat, ErrorEvent, Message, Update

from app.bot import errors as errors_module
from app.bot.commands import BOT_COMMANDS, build_bot_commands, register_commands
from app.bot.errors import on_error


def test_bot_commands_invariants():
    names = [name for name, _desc in BOT_COMMANDS]
    assert len(names) == len(set(names)), "имена команд уникальны"
    assert all(name.islower() and 1 <= len(name) <= 32 and " " not in name for name in names)
    assert all(desc.strip() for _name, desc in BOT_COMMANDS), "у каждой команды есть описание"
    assert {"start", "help", "stats", "buy", "knowledge", "privacy", "cancel", "forget_me"} <= set(
        names
    )


def test_build_bot_commands_order_preserved():
    commands = build_bot_commands()
    assert [c.command for c in commands] == [name for name, _ in BOT_COMMANDS]
    assert commands[0].command == "start"


async def test_register_commands_calls_api():
    class FakeBot:
        def __init__(self) -> None:
            self.commands = None

        async def set_my_commands(self, commands):
            self.commands = commands

    bot = FakeBot()
    assert await register_commands(bot) is True
    assert bot.commands is not None and len(bot.commands) == len(BOT_COMMANDS)


async def test_register_commands_survives_network_failure():
    class BrokenBot:
        async def set_my_commands(self, commands):
            raise RuntimeError("network down")

    assert await register_commands(BrokenBot()) is False


def _error_event(chat_id: int = 555) -> ErrorEvent:
    chat = Chat(id=chat_id, type="private")
    message = Message(message_id=1, date=datetime.now(UTC), chat=chat, text="привет")
    return ErrorEvent(update=Update(update_id=1, message=message), exception=RuntimeError("boom"))


async def test_on_error_notifies_user_once(settings):
    errors_module._last_notify.clear()
    sent: list[tuple[int, str]] = []

    class FakeBot:
        async def send_message(self, chat_id: int, text: str):
            sent.append((chat_id, text))
            chat = Chat(id=chat_id, type="private")
            return Message(message_id=2, date=datetime.now(UTC), chat=chat, text=text)

    ok = await on_error(_error_event(), bot=FakeBot(), settings=settings)
    assert ok is True
    assert sent and sent[0][0] == 555
    assert "не так" in sent[0][1]


async def test_on_error_respects_cooldown(settings):
    errors_module._last_notify.clear()
    sent: list[int] = []

    class FakeBot:
        async def send_message(self, chat_id: int, text: str):
            sent.append(chat_id)
            chat = Chat(id=chat_id, type="private")
            return Message(message_id=2, date=datetime.now(UTC), chat=chat, text=text)

    bot = FakeBot()
    await on_error(_error_event(), bot=bot, settings=settings)
    await on_error(_error_event(), bot=bot, settings=settings)
    assert sent == [555], "второе уведомление подавлено анти-спамом"

    errors_module._last_notify.clear()


async def test_on_error_survives_broken_notify(settings):
    errors_module._last_notify.clear()

    class BrokenBot:
        async def send_message(self, chat_id: int, text: str):
            raise RuntimeError("bot blocked")

    assert await on_error(_error_event(), bot=BrokenBot(), settings=settings) is True


async def test_on_error_without_chat_is_silent(settings):
    errors_module._last_notify.clear()
    event = ErrorEvent(update=Update(update_id=2), exception=RuntimeError("no chat"))
    assert await on_error(event, bot=None, settings=settings) is True


def test_support_username_rendered(settings):
    from app.bot import texts

    custom = settings.model_copy(update={"support_username": "@helpdesk"})
    assert "@helpdesk" in texts.help_text(custom)
    assert "@helpdesk" in texts.privacy_text(custom)
    assert "Поддержка" not in texts.help_text(settings)  # не задан — строки нет