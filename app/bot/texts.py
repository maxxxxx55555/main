"""Все тексты бота — единый источник копирайта.

Правила:
- тексты собираются функциями: цены/лимиты берутся из каталога, а не хардкодятся;
- пользовательские данные (имена) вставляются только через escape_html;
- HTML-разметка ограничена тегами <b>/<i>/<code>/<a> — они проходят parse_mode=HTML.
"""

from __future__ import annotations

from app.config import Settings
from app.services.billing.plans import PlanCatalog
from app.utils.text import escape_html

# --- Общие приветствия и справка ---


def welcome(name: str, catalog: PlanCatalog) -> str:
    """Приветственное сообщение с акцентом на premium-фичи: лиды, персоны, RAG."""
    free = catalog.get("free")
    pro = catalog.get("pro")
    return (
        f"👋 Привет, <b>{escape_html(name)}</b>!\n\n"
        "Я — <b>AI-Сотрудник</b>, ваш персональный AI-ассистент для бизнеса.\n"
        "💼 Отвечаю клиентам 24/7 · 🎯 Квалифицирую лидов и сохраняю в CRM · "
        "📋 Записываю на консультации\n\n"
        "<b>Что я умею</b>\n"
        "• Отвечать на вопросы по вашей базе знаний (PRO/Business)\n"
        "• Автоматически выявлять и сохранять лидов из диалогов\n"
        "• Работать в одной из AI-персон (реалтор, e-commerce, консультант...)\n"
        "• Помогать настраивать ответы под ваш бренд\n\n"
        f"💡 <b>Старт: {free.message_limit} сообщений/мес бесплатно</b>, без карты.\n"
        f"🚀 PRO (⭐{pro.price_stars}): {pro.message_limit} сообщений + RAG + приоритет\n"
        "Администратор может настроить персону через /adminpersona"
    )


def _support_line(settings: Settings) -> str:
    username = settings.support_username.strip().lstrip("@")
    return f"\n\n📮 Поддержка: @{username}" if username else ""


def help_text(settings: Settings) -> str:
    """Справка с упоминанием премиум-фич: лиды, AI-персоны."""
    catalog_note = "PRO и Business: /buy"
    return (
        "🤖 <b>AI-Сотрудник — ваш персональный AI-ассистент</b>\n\n"
        "<b>Что я делаю</b>\n"
        "• 💬 Отвечаю клиентам 24/7 по вашей базе знаний (PRO/Business)\n"
        "• 🎯 Автоматически выявляю и сохраняю лидов из диалогов\n"
        "• 📋 Помогаю записывать клиентов на консультацию\n"
        "• 🎭 Работаю в AI-персонах (реалтор, e-commerce, консультант...)\n\n"
        "<b>Команды</b>\n"
        "/start — начать работу\n"
        "/help — эта справка\n"
        "/stats — тариф и остаток лимита\n"
        f"/buy — тарифы и оплата (Telegram Stars) — {catalog_note}\n"
        "/knowledge — база знаний: бот отвечает от лица вашего бизнеса\n"
        "/privacy — как хранятся ваши данные\n"
        "/cancel — отменить текущее действие\n"
        "/forget_me — удалить все мои данные\n\n"
        "💬 Напишите вопрос — я отвечу как сотрудник вашего бизнеса.\n"
        "📄 Базу знаний загружайте текстом или .txt/.md файлом."
        f"{_support_line(settings)}"
    )


def privacy_text(settings: Settings) -> str:
    return (
        "🔐 <b>Как хранятся ваши данные</b>\n\n"
        "• Профиль: Telegram ID, тариф, расход лимита — для работы бота.\n"
        "• История диалогов — чтобы я помнил контекст беседы. "
        "Старые сообщения автоматически удаляются по retention-политике.\n"
        "• База знаний — только на PRO/Business, видна только вам.\n"
        "• Тексты сообщений передаются LLM-провайдеру для генерации ответов.\n"
        "• Оплата проходит через Telegram Stars — реквизиты карты я не вижу и не храню.\n\n"
        "🗑 Команда /forget_me удаляет <b>всё</b>: профиль, историю, базу знаний — "
        "безвозвратно и сразу."
        f"{_support_line(settings)}"
    )


def knowledge_intro(can_upload: bool, max_len: int, max_file_kb: int = 256) -> str:
    base = (
        "📚 <b>База знаний</b>\n\n"
        "Загрузите FAQ, цены, условия работы, скрипты продаж — я буду отвечать "
        "клиентам строго по этим данным, а не выдумывать.\n\n"
        "▫️ Отправьте текст одним сообщением (до "
        f"{max_len} символов) или файлом .txt / .md до {max_file_kb} КБ."
    )
    if not can_upload:
        return base + "\n\n🔒 База знаний доступна на тарифах PRO и Business — /buy"
    return base


# --- Короткие ответы ---

ASK_HINT = "💬 Просто напишите ваш вопрос следующим сообщением — я отвечу 🙂"

NOT_TEXT = (
    "✋ Я понимаю текстовые сообщения (а на PRO — ещё и .txt/.md файлы для базы знаний).\n"
    "Напишите вопрос текстом 🙂"
)

UNKNOWN_COMMAND = "🤔 Не знаю такой команды. Полный список — /help"

# --- Group chat texts ---
NOT_ADMIN = "⛔️ Только администраторы чата могут использовать эту команду."

DEFAULT_WELCOME_GROUP = "👋 Добро пожаловать, {name}! 👋\n\n" \
    "📚 Правила чата доступны по /rules\n" \
    "💬 Пишем по делу, уважаем друг друга.\n" \
    "🎯 Активность учитывается — топ на /top"


def chat_stats(stats: dict[str, int]) -> str:
    """Статистика активности чата."""
    total = stats.get("total_messages", 0)
    active = stats.get("active_users", 0)
    active_week = stats.get("active_week", 0)
    return (
        f"📊 <b>Статистика чата</b>\n\n"
        f"Всего сообщений: <b>{total}</b>\n"
        f"Активных участников: <b>{active}</b>\n"
        f"Активных за неделю: <b>{active_week}</b>\n\n"
        "🏆 Рейтинг: /top · 🔄 Сбросить: /resetactivity"
    )


# --- AI Group Bot texts ---

AI_MODERATION_SPOOF = "🛡️ <b>AI-модерация включена</b>\n\n" \
    "ИИ проверяет семантику сообщений, а не только ключевые слова."

AI_SENTIMENT_POSITIVE = "😊 Позитивный"
AI_SENTIMENT_NEUTRAL = "😐 Нейтральный"
AI_SENTIMENT_NEGATIVE = "😠 Негативный"


def sentiment_label(sentiment: str, compound: float) -> str:
    """Человекочитаемая метка тональности."""
    labels = {
        "positive": AI_SENTIMENT_POSITIVE,
        "neutral": AI_SENTIMENT_NEUTRAL,
        "negative": AI_SENTIMENT_NEGATIVE,
    }
    base = labels.get(sentiment, AI_SENTIMENT_NEUTRAL)
    return f"{base} (оценка: {compound:+.2f})"


def chat_summary_text(summary: str, topics: list[str], action_items: list[str], sentiment: str) -> str:
    """Текст резюме чата."""
    lines = ["📋 <b>AI-резюме чата</b>\n"]
    lines.append(f"<b>Сводка:</b> {summary}\n")
    if topics:
        lines.append(f"<b>Темы:</b> {', '.join(topics)}\n")
    if action_items:
        lines.append(f"<b>Задачи:</b> {', '.join(action_items)}\n")
    lines.append(f"<b>Тональность:</b> {sentiment_label(sentiment, 0)}")
    return "\n".join(lines)


def ai_error_msg() -> str:
    """Сообщение об ошибке ИИ."""
    return "😔 AI-сервис временно недоступен. Попробуйте позже."

LLM_DOWN = (
    "😔 Сервис AI временно недоступен, попробуйте через несколько минут.\n"
    "Ваш лимит не списан."
)

THROTTLE_WARNING = "🐢 Слишком много сообщений подряд. Подождите минуту, пожалуйста."

NEED_PLAN = "📚 База знаний доступна на тарифах PRO и Business. Подключите в разделе тарифов."

CANCEL_DONE = "Отменено. Чем ещё помочь?"


def limit_reached(reset_date: str) -> str:
    return (
        "🚧 Лимит сообщений на текущий период исчерпан.\n"
        f"Лимит обновится {reset_date}."
    )


def message_too_long(max_len: int) -> str:
    return f"✋ Сообщение слишком длинное (максимум {max_len} символов). Разбейте его на части."


def knowledge_saved(chunks: int) -> str:
    return (
        f"✅ Сохранено фрагментов базы знаний: <b>{chunks}</b>.\n"
        "Теперь я отвечаю клиентам по этим данным. Задайте тестовый вопрос!"
    )


def knowledge_file_saved(chunks: int, filename: str) -> str:
    return (
        f"✅ Файл «{escape_html(filename)}» загружен: <b>{chunks}</b> фрагментов.\n"
        "Задайте тестовый вопрос клиента — проверьте ответы."
    )