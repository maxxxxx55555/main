"""Тесты AI-фич группового чата."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update
from aiogram.types import User as TgUser

from app.services.ai.moderation import (
    ChatAnalyzer, ModerationResult, SentimentResult, ChatSummary,
)
from app.services.ai.provider import Reply
from app.services.ai.moderation import ModerationService, SentimentService


class MockProvider:
    """Mock AI provider для тестов."""
    def __init__(self):
        self.calls = []
    async def chat(self, messages):
        self.calls.append(messages)
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if "summary" in last.lower():
            return Reply('{"summary": "test", "sentiment_overall": "positive"}', 50)
        if "translate" in last.lower() or "переведи" in last.lower():
            return Reply("Переведенный текст", 20)
        if "positive" in last.lower():
            return Reply('{"sentiment": "positive", "compound": 0.7, "language": "ru"}', 30)
        if "negative" in last.lower():
            return Reply('{"sentiment": "negative", "compound": -0.5, "language": "en"}', 30)
        return Reply('{"sentiment": "neutral", "compound": 0.0, "language": "ru"}', 30)
    async def embed(self, texts):
        return [[0.0] * 64 for _ in texts]


@pytest.mark.asyncio
async def test_moderation_detects_links():
    svc = ModerationService(MockProvider())
    r = await svc.moderate("Проверьте http://example.com")
    assert r.verdict == "ads"
    assert "Ссылка" in r.reason


@pytest.mark.asyncio
async def test_moderation_ok_text():
    svc = ModerationService(MockProvider())
    r = await svc.moderate("Привет, как дела?")
    assert 0.0 <= r.confidence <= 1.0


@pytest.mark.asyncio
async def test_sentiment_positive():
    svc = SentimentService(MockProvider())
    r = await svc.analyze("Это замечательно!")
    assert r.sentiment == "positive"
    assert r.language == "ru"


@pytest.mark.asyncio
async def test_sentiment_llm_error():
    from app.services.ai.provider import LLMUnavailable
    class ErrProvider:
        async def chat(self, messages):
            raise LLMUnavailable("test")
    svc = SentimentService(ErrProvider())
    r = await svc.analyze("Тест")
    assert r.sentiment == "neutral"
    assert r.compound == 0.0
    assert r.language == "unknown"


@pytest.mark.asyncio
async def test_chat_analyzer_summary():
    analyzer = ChatAnalyzer(MockProvider())
    r = await analyzer.summarize(messages=["Привет"], max_messages=10)
    assert isinstance(r.summary, str)


@pytest.mark.asyncio
async def test_dataclasses():
    r = ModerationResult("ok", 0.95, "чисто")
    assert r.verdict == "ok"
    s = SentimentResult("negative", -0.8, "ru")
    assert s.sentiment == "negative"
    cs = ChatSummary("t", ["a"], ["b"], "neutral")
    assert cs.topics == ["a"]


@pytest.mark.asyncio
async def test_ai_group_texts():
    from app.bot import texts
    assert "AI-модерация" in texts.AI_MODERATION_SPOOF
    assert "Сбросить" in texts.chat_stats({"total_messages": 100, "active_users": 10, "active_week": 5})
    label = texts.sentiment_label("positive", 0.75)
    assert "Позитивный" in label
    summary = texts.chat_summary_text("t", ["тема1"], ["задача1"], "positive")
    assert "резюме" in summary.lower()
    assert "недоступен" in texts.ai_error_msg()


@pytest.mark.asyncio
async def test_group_handlers_registered():
    from app.bot.handlers.group import router
    handler_names = [h.callback.__name__ for h in router.message.handlers]
    assert "cmd_sentiment" in handler_names
    assert "cmd_translate" in handler_names
    assert "cmd_aimod" in handler_names
    assert "cmd_summarise" in handler_names
