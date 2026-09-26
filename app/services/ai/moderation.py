"""AI-модерация: проверка текста на нарушения через LLM.

Premium feature: ИИ анализирует семантику, а не только ключевые слова.
Поддерживает: спам, токсичность, реклама, NSFW.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Literal

from app.services.ai.provider import AIProvider, LLMUnavailable

logger = logging.getLogger(__name__)

ModerationVerdict = Literal["ok", "spam", "toxic", "ads", "nsfw"]


@dataclass(frozen=True)
class ModerationResult:
    verdict: ModerationVerdict
    confidence: float  # 0.0 - 1.0
    reason: str


_MODERATION_PROMPT = """Проскрись текст на нарушения. Ответ строго в JSON:
{"verdict": "ok|spam|toxic|ads|nsfw", "confidence": 0-1, "reason": "кратко"}

Критерии:
- spam: реклама, флуд, повторения
- toxic: уничижительные высказательства, агрессия, оскорбления
- ads: рекламные ссылки, промо-контент
- nsfw: неподходящий контент

Текст: """


class ModerationService:
    """AI-модерация текста через LLM."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def moderate(self, text: str, context: str | None = None) -> ModerationResult:
        """Проверяет текст на нарушения."""
        if "http://" in text or "https://" in text:
            return ModerationResult("ads", 0.9, "Ссылка в сообщении")

        prompt = _MODERATION_PROMPT + text
        if context:
            prompt = f"Контекст чата: {context}\n\n" + prompt

        try:
            reply = await self.provider.chat([
                {"role": "system", "content": "Ты -- модератор чата. Отвечай только JSON."},
                {"role": "user", "content": prompt},
            ])
            data = json.loads(reply.content.strip().strip("```"))
            return ModerationResult(
                verdict=data.get("verdict", "ok"),
                confidence=float(data.get("confidence", 0)),
                reason=data.get("reason", ""),
            )
        except (LLMUnavailable, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Moderation LLM failed: %s", e)
            return ModerationResult("ok", 0.0, "LLM недоступен, проверка пропущена")
        except Exception:
            logger.exception("Unexpected moderation error")
            return ModerationResult("ok", 0.0, "Ошибка проверки")


@dataclass(frozen=True)
class SentimentResult:
    """Результат анализа тональности сообщения."""
    sentiment: Literal["positive", "neutral", "negative"]
    compound: float
    language: str


_SENTIMENT_PROMPT = """Определи тональность текста. Ответ строго в JSON:
{"sentiment": "positive|neutral|negative", "compound": -1.0..1.0, "language": "ru|en|..."}

Текст: """


class SentimentService:
    """AI-анализ тональности текста через LLM."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def analyze(self, text: str) -> SentimentResult:
        """Определяет тональность текста."""
        prompt = _SENTIMENT_PROMPT + text

        try:
            reply = await self.provider.chat([
                {"role": "system", "content": "Ты -- аналитик тональности текста. Отвечай только JSON."},
                {"role": "user", "content": prompt},
            ])
            data = json.loads(reply.content.strip().strip("```"))
            return SentimentResult(
                sentiment=data.get("sentiment", "neutral"),
                compound=float(data.get("compound", 0)),
                language=data.get("language", "ru"),
            )
        except (LLMUnavailable, json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            logger.warning("Sentiment LLM failed: %s", e)
            return SentimentResult("neutral", 0.0, "unknown")


@dataclass(frozen=True)
class ChatSummary:
    """Результат анализа чата."""
    summary: str
    topics: list[str]
    action_items: list[str]
    sentiment_overall: Literal["positive", "neutral", "negative"]


_SUMMARY_PROMPT = """Проанализируй сообщения группового чата и выдай JSON:
{"summary": "краткое резюме", "topics": ["тема1", "тема2"], "action_items": ["задача1"], "sentiment_overall": "positive|neutral|negative"}

Сообщения:
"""


class ChatAnalyzer:
    """AI-анализ чата: резюме, темы, задачи, тональность."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    async def summarize(self, messages: list[str], max_messages: int = 50) -> ChatSummary:
        """Создаёт резюме чата из сообщений."""
        recent = messages[-max_messages:]
        combined = "\n".join(recent)

        try:
            reply = await self.provider.chat([
                {"role": "system", "content": "Ты -- аналитик чат-менеджера. Выводи только JSON."},
                {"role": "user", "content": _SUMMARY_PROMPT + combined},
            ])
            data = json.loads(reply.content.strip().strip("```"))
            return ChatSummary(
                summary=data.get("summary", ""),
                topics=data.get("topics", []),
                action_items=data.get("action_items", []),
                sentiment_overall=data.get("sentiment_overall", "neutral"),
            )
        except (LLMUnavailable, json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            logger.warning("Chat summary LLM failed: %s", e)
            return ChatSummary("Ошибка анализа", [], [], "neutral")
