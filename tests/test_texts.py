"""Тексты бота: динамические цены, экранирование, обязательные ссылки."""

from __future__ import annotations

from app.bot import texts
from app.services.billing.plans import PlanCatalog


def test_welcome_escapes_user_name(settings):
    catalog = PlanCatalog(settings)
    body = texts.welcome("<b>Evil</b> & Co", catalog)
    assert "&lt;b&gt;Evil&lt;/b&gt; &amp; Co" in body
    assert "<b>Evil</b>" not in body  # инъекция невозможна


def test_welcome_uses_catalog_values(settings):
    catalog = PlanCatalog(settings)
    body = texts.welcome("Аня", catalog)
    free = catalog.get("free")
    pro = catalog.get("pro")
    assert f"{free.message_limit} сообщений" in body
    assert f"⭐{pro.price_stars}" in body
    assert f"{pro.message_limit} сообщений" in body


def test_help_lists_all_public_commands(settings):
    body = texts.help_text(settings)
    for command in ("/start", "/help", "/stats", "/buy", "/knowledge", "/privacy", "/cancel", "/forget_me"):
        assert command in body, f"в справке нет команды {command}"


def test_privacy_explains_data_and_deletion(settings):
    body = texts.privacy_text(settings)
    assert "/forget_me" in body
    assert "Stars" in body  # как проходят платежи
    assert "LLM" in body  # куда уходят сообщения


def test_knowledge_intro_reflects_plan_and_limit(settings):
    free_body = texts.knowledge_intro(can_upload=False, max_len=settings.max_message_len)
    assert "PRO" in free_body and "🔒" in free_body
    pro_body = texts.knowledge_intro(can_upload=True, max_len=settings.max_message_len)
    assert str(settings.max_message_len) in pro_body
    assert ".txt" in pro_body and ".md" in pro_body


def test_limit_and_length_messages(settings):
    assert "01.01.2026" in texts.limit_reached("01.01.2026")
    assert str(settings.max_message_len) in texts.message_too_long(settings.max_message_len)
    assert "3" in texts.knowledge_saved(3)


def test_knowledge_file_saved_escapes_filename():
    body = texts.knowledge_file_saved(5, "<script>.txt")
    assert "&lt;script&gt;.txt" in body
    assert "<script>" not in body
