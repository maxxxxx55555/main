"""HTML-безопасность и разбиение сообщений (utils/text.py)."""

from __future__ import annotations

from app.utils.text import escape_html, format_reply, to_telegram_html


def test_escape_html_basic():
    assert escape_html("a < b & c > d") == "a &lt; b &amp; c &gt; d"
    assert escape_html('кавычки "x" и \'y\'') == 'кавычки "x" и \'y\''  # quote=False


def test_to_telegram_html_escapes_injection():
    """Главный инвариант: произвольный текст не может внедрить HTML-теги."""
    out = to_telegram_html("<script>alert('x')</script> <b>не наш тег</b>")
    assert "<script>" not in out and "</script>" not in out
    assert "&lt;script&gt;" in out and "&lt;b&gt;не наш тег&lt;/b&gt;" in out


def test_to_telegram_html_markdown_lite():
    assert to_telegram_html("**важно**") == "<b>важно</b>"
    assert to_telegram_html("код `print(1)` тут") == "код <code>print(1)</code> тут"
    assert to_telegram_html("```\nline1\nline2\n```") == "<pre>line1\nline2</pre>"
    assert to_telegram_html("# Заголовок") == "<b>Заголовок</b>"
    assert to_telegram_html("- первый\n- второй") == "• первый\n• второй"


def test_to_telegram_html_code_block_keeps_markdown_inside():
    """Внутри <pre> разметка не применяется — иначе код превращается в мусор."""
    out = to_telegram_html("```\n**не жирный** `не код`\n```")
    assert out == "<pre>**не жирный** `не код`</pre>"


def test_format_reply_empty_and_short():
    assert format_reply("") == []
    assert format_reply("   ") == []
    assert format_reply("Привет") == ["Привет"]


def test_format_reply_splits_long_text_by_limit():
    text = ("Предложение номер один. " * 500).strip()  # ~12k символов
    parts = format_reply(text, limit=1000)
    assert len(parts) >= 2
    assert all(len(p) <= 1000 for p in parts)
    # Текст не потерян: склейка частей содержит ключевые слова
    assert "Предложение" in parts[0]
    assert all("Предложение" in p for p in parts)


def test_format_reply_hard_split_long_monolith():
    text = "x" * 9500  # без пробелов: разбивается жёстко, но без потерь
    parts = format_reply(text, limit=4000)
    assert len(parts) == 3
    assert all(len(p) <= 4000 for p in parts)
    assert sum(len(p) for p in parts) == 9500


def test_format_reply_keeps_markdown_across_parts():
    text = ("**важный пункт** и немного текста. " * 100).strip()
    parts = format_reply(text, limit=500)
    assert len(parts) > 1
    for part in parts:
        # Каждая часть — валидный HTML (теги парные, не разрезаны)
        assert part.count("<b>") == part.count("</b>")


def test_format_reply_normalizes_blank_lines():
    assert format_reply("a\n\n\n\nb") == ["a\n\nb"]
