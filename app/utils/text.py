"""Безопасный вывод в Telegram: экранирование, markdown-lite и разбиение сообщений.

Главный инвариант: **любой** текст (в т.ч. сгенерированный LLM) обязан пройти
через `format_reply`, прежде чем попасть в сообщение с parse_mode=HTML.
Прямая вставка внешнего текста в HTML-сообщение — источник ошибок
«can't parse entities» из-за символов `<`, `>`, `&`.

Поддерживаемый markdown-lite (то, что реально используют LLM):
- ```...```   → <pre>...</pre>
- `code`      → <code>code</code>
- **bold**    → <b>bold</b>
- # Заголовок → <b>Заголовок</b>
- "- пункт"   → "• пункт"
"""

from __future__ import annotations

import html
import re

# Лимит Telegram на длину одного сообщения — 4096; оставляем запас под правки.
SAFE_MESSAGE_LIMIT = 4000

_MAX_BLANK_LINES = re.compile(r"\n{3,}")
_CODE_FENCE = re.compile(r"```([^`]*(?:`(?!``)[^`]*)*)```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
_HEADING = re.compile(r"^(?:#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_BULLET = re.compile(r"^[ \t]*[-–—][ \t]+", re.MULTILINE)
_HTML_TAG = re.compile(r"</?(b|strong|i|em|u|s|code|pre|a)\b[^>]*>", re.IGNORECASE)


def escape_html(text: str) -> str:
    """Экранирует &, <, > — безопасно для parse_mode=HTML."""
    return html.escape(text, quote=False)


def to_telegram_html(text: str) -> str:
    """Markdown-lite → Telegram HTML. Безопасен: сначала экранирование, потом теги.

    Код-блоки защищены плейсхолдерами: внутри <pre>/<code> разметка не применяется.
    """
    escaped = escape_html(text)

    protected: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        protected.append(f"<pre>{match.group(1).strip()}</pre>")
        return f"\x00{len(protected) - 1}\x00"

    escaped = _CODE_FENCE.sub(_stash, escaped)
    escaped = _INLINE_CODE.sub(r"<code>\1</code>", escaped)
    escaped = _BOLD.sub(r"<b>\1</b>", escaped)
    escaped = _HEADING.sub(r"<b>\1</b>", escaped)
    escaped = _BULLET.sub("• ", escaped)

    def _restore(match: re.Match[str]) -> str:
        return protected[int(match.group(1))]

    return re.sub(r"\x00(\d+)\x00", _restore, escaped)


def _tags_balanced(text: str) -> bool:
    """Проверка парности поддерживаемых тегов (страховка после разбиения)."""
    counts: dict[str, int] = {}
    for match in _HTML_TAG.finditer(text):
        tag = match.group(1).lower()
        if tag == "strong":
            tag = "b"
        elif tag == "em":
            tag = "i"
        if match.group(0).startswith("</"):
            counts[tag] = counts.get(tag, 0) - 1
        else:
            counts[tag] = counts.get(tag, 0) + 1
    return all(value == 0 for value in counts.values())


def _split_plain(text: str, limit: int) -> list[str]:
    """Режет исходный (не-HTML) текст по «приятным» границам: абзац → строка → предложение."""
    parts: list[str] = []
    rest = text
    while len(rest) > limit:
        window = rest[:limit]
        cut = -1
        for boundary in ("\n\n", "\n", ". ", "! ", "? ", " "):
            pos = window.rfind(boundary)
            if pos > limit // 3:
                cut = pos + len(boundary)
                break
        if cut <= 0:
            cut = limit  # сверхдлинный монолит (например, base64) — режем жёстко
        parts.append(rest[:cut].strip())
        rest = rest[cut:].lstrip()
    if rest:
        parts.append(rest)
    return [p for p in parts if p]


def format_reply(text: str, limit: int = SAFE_MESSAGE_LIMIT) -> list[str]:
    """Единая точка подготовки ответа к отправке.

    Возвращает список частей, каждая ≤ limit, готовая к `answer(parse_mode=HTML)`.
    Части, где разметка оказалась разорвана разбиением, безопасно сбрасываются
    в чистый экранированный текст.
    """
    normalized = _MAX_BLANK_LINES.sub("\n\n", (text or "").strip())
    if not normalized:
        return []
    chunks = _split_plain(normalized, limit) if len(normalized) > limit else [normalized]
    rendered: list[str] = []
    for chunk in chunks:
        candidate = to_telegram_html(chunk)
        rendered.append(candidate if _tags_balanced(candidate) else escape_html(chunk))
    return rendered
