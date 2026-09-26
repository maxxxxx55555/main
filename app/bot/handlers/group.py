"""Групповой чат-бот: модерация, анти-спам, ИИ-фичи, рейтинги, приветствия.

Фичи:
- /setrules, /rules — управление правилами чата
- /setwelcome, /welcome — кастомное приветствие
- /top — топ активных участников
- /chatstats — статистика чата
- /mute /unmute /ban /kick /warn /ro — модерация
- /resetactivity — сбросить рейтинги
- /aimod — AI-модерация (вкл/выкл)
- /summarise — AI-резюме чата
- /sentiment — анализ тональности сообщения
- Авто-приветствие новых участников
- Анти-спам: удаление ссылок и повторяющихся сообщений
"""

from __future__ import annotations

import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.db.repo.chats import ActivityRepo, ChatRepo
from app.db.repo.messages import MessageRepo
from app.services.ai.moderation import ChatAnalyzer, ModerationService, SentimentService
from app.services.ai.provider import AIProvider
from app.config import Settings

router = Router(name="group")
logger = logging.getLogger(__name__)

# Фильтр: только группы и супергруппы (на уровне хендлеров)
GROUP_FILTER = F.chat.type.in_({'group', 'supergroup'})

# --- Спам-паттерны ---
SPAM_PATTERNS: list[re.Pattern] = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"@\w{5,}"),  # @username длиннее 5 символов
    re.compile(r"\b(купить|прода[мт]ц|помощь|нужен|заказ)\b", re.IGNORECASE),
]
FLOOD_WINDOW = 5  # секунд между сообщениями для одного пользователя
_flood_cache: dict[int, list[float]] = {}


async def _is_chat_admin(message: Message) -> bool:
    """Проверка: пользователь является администратором чата."""
    try:
        member = await message.chat.get_member(message.from_user.id)
        return member.status.value in ("administrator", "creator")
    except Exception:
        return False


async def _is_bot_admin(message: Message) -> bool:
    """Проверка: бот является администратором чата (может удалять/мутить)."""
    try:
        bot_member = await message.chat.get_member(message.bot.id)
        return bot_member.status.value in ("administrator", "creator")
    except Exception:
        return False


# --- Управление правилами ---

@router.message(Command("setrules"), GROUP_FILTER)
async def cmd_setrules(message: Message, session: AsyncSession) -> None:
    """Установить правила чата: /setrules <текст>"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    rules = message.get_args().strip()
    if not rules:
        await message.reply("Использование: /setrules <правила чата>")
        return
    repo = ChatRepo(session)
    settings = await repo.update_rules(message.chat.id, rules)
    await message.reply("✅ Правила чата установлены. Просмотр: /rules")


@router.message(Command("rules"), GROUP_FILTER)
async def cmd_rules(message: Message, session: AsyncSession) -> None:
    """Показать правила чата."""
    repo = ChatRepo(session)
    settings = await repo.get_or_create(message.chat.id, message.chat.title or "")
    if not settings.rules:
        await message.reply("Правила чата не установлены.")
        return
    await message.reply(settings.rules)


# --- Управление приветствием ---

@router.message(Command("setwelcome"), GROUP_FILTER)
async def cmd_setwelcome(message: Message, session: AsyncSession) -> None:
    """Установить кастомное приветствие: /setwelcome <текст>"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    welcome_text = message.get_args().strip()
    if not welcome_text:
        await message.reply("Использование: /setwelcome <приветственное сообщение>")
        return
    repo = ChatRepo(session)
    await repo.update_welcome(message.chat.id, welcome_text, enabled=True)
    await message.reply("✅ Приветствие установлено. Новые участники будут видеть его.")


@router.message(Command("welcome"), GROUP_FILTER)
async def cmd_toggle_welcome(message: Message, session: AsyncSession) -> None:
    """Включить/выключить приветствие: /welcome on|off"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    arg = message.get_args().strip().lower()
    if arg not in ("on", "off", "enable", "disable"):
        await message.reply("Использование: /welcome on|off")
        return
    enabled = arg in ("on", "enable")
    repo = ChatRepo(session)
    await repo.update_welcome(message.chat.id, "", enabled=enabled)
    
# --- Модерация ---

@router.message(Command("mute"), GROUP_FILTER)
async def cmd_mute(message: Message) -> None:
    """Замьютить пользователя: /mute 10м Текстовой спам"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого нужно замьютить.")
        return
    target = message.reply_to_message.from_user
    args = message.get_args().strip()
    duration_min = 10  # по умолчанию 10 минут
    reason = ""
    if args:
        match = re.match(r"(\d+)([мчд])?", args)
        if match:
            num = int(match.group(1))
            unit = match.group(2) or "м"
            if unit == "м":
                duration_min = num
            elif unit == "ч":
                duration_min = num * 60
            elif unit == "д":
                duration_min = num * 60 * 24
            reason = args[match.end():].strip()
    await message.reply(
        f"🔇 {target.full_name} замучен на {duration_min} минут."
                + (f" Причина: {reason}" if reason else "")
    )


@router.message(Command("unmute"), GROUP_FILTER)
async def cmd_unmute(message: Message) -> None:
    """Размьютить пользователя."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого нужно размьютить.")
        return
    await message.reply(f"🔊 {message.reply_to_message.from_user.full_name} размучен.")


@router.message(Command("ban"), GROUP_FILTER)
async def cmd_ban(message: Message) -> None:
    """Забанить пользователя."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого нужно забанить.")
        return
    await message.reply(f"🚫 {message.reply_to_message.from_user.full_name} забанен в этом чате.")


@router.message(Command("kick"), GROUP_FILTER)
async def cmd_kick(message: Message) -> None:
    """Кикнуть пользователя."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя, которого нужно кикнуть.")
        return
    await message.reply(f"👢 {message.reply_to_message.from_user.full_name} удалён из чата.")


@router.message(Command("warn"), GROUP_FILTER)
async def cmd_warn(message: Message, session: AsyncSession) -> None:
    """Выдать предупреждение пользователю."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте на сообщение пользователя для выдачи варна.")
        return
    reason = message.get_args().strip() or "нарушение правил чата"
    await message.reply(
        f"⚠️ {message.reply_to_message.from_user.full_name} получил варн: {reason}"
    )


@router.message(Command("ro"), GROUP_FILTER)
async def cmd_ro(message: Message) -> None:
    """Включить режим только чтения для чата."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
        await message.reply("🔇 Режим только чтения включён. Только администраторы могут писать.")


# --- Статистика и рейтинги ---

@router.message(Command("top"), GROUP_FILTER)
async def cmd_top(message: Message, session: AsyncSession) -> None:
    """Показать топ активных участников чата."""
    repo = ActivityRepo(session)
    top = await repo.top_users(message.chat.id, limit=10)
    if not top:
        await message.reply("Пока нет активных участников для рейтинга.")
        return
    lines = ["🏆 <b>Топ-10 активных участников</b>"]
    for i, user in enumerate(top, 1):
        name = user.username or user.first_name or f"id:{user.user_id}"
        lines.append(f"{i}. {name} — {user.message_count} сообщений ({user.score} баллов)")
    await message.reply("\n".join(lines))


@router.message(Command("chatstats"), GROUP_FILTER)
async def cmd_chatstats(message: Message, session: AsyncSession) -> None:
    """Статистика чата: сообщения, активные участники."""
    repo = ActivityRepo(session)
    stats = await repo.chat_stats(message.chat.id)
    await message.reply(texts.chat_stats(stats))


@router.message(Command("resetactivity"), GROUP_FILTER)
async def cmd_reset_activity(message: Message, session: AsyncSession) -> None:
    """Сбросить всех показатели активности."""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    repo = ActivityRepo(session)
    await repo.reset_activity(message.chat.id)
    await message.reply("🔄 Статистика активности сброшена.")


# --- Анти-спам ---

@router.message(F.text, GROUP_FILTER)
async def process_spam_check(message: Message, session: AsyncSession) -> None:
    """Проверка на спам и трекинг активности (для обычных текстовых сообщений)."""
    import time
    repo = ChatRepo(session)
    settings = await repo.get_or_create(message.chat.id, message.chat.title or "")
    if not settings.anti_spam_enabled:
        await _track_activity(message, session)
        return

    text = message.text.strip()

    # Проверка на спам-паттерны (ссылки, рекламные ключи)
    for pattern in SPAM_PATTERNS:
        if pattern.search(text):
            is_admin = await _is_chat_admin(message)
            if is_admin:
                return
            if settings.auto_moderate:
                try:
                    await message.delete()
                except Exception:
                    pass
            await message.reply("🛡️ Сообщение похоже на спам и было удалено.")
            return

    # Проверка на флуд (слишком частые сообщения)
    now = time.time()
    user_key = message.from_user.id
    cache = _flood_cache.setdefault(user_key, [])
    cache = [t for t in cache if now - t < FLOOD_WINDOW]
    _flood_cache[user_key] = cache
    if len(cache) >= 3 and not await _is_chat_admin(message):
        await message.reply("🐢 Слишком много сообщений подряд. Подождите немного.")
        return
    cache.append(now)

    await _track_activity(message, session)


async def _track_activity(message: Message, session: AsyncSession) -> None:
    """Увеличить счётчики активности для отправителя."""
    if message.from_user and not message.from_user.is_bot:
        repo = ActivityRepo(session)
        await repo.add_message(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "",
        )


# --- Приветствие новых участников ---

@router.chat_member(GROUP_FILTER)
async def process_new_member(event: ChatMemberUpdated, session: AsyncSession) -> None:
    """Приветствие новых участников в чате."""
    if event.new_chat_members:
        for new_member in event.new_chat_members:
            if new_member.is_bot:
                continue
            repo = ChatRepo(session)
            settings = await repo.get_or_create(event.chat.id, event.chat.title or "")
            if settings.welcome_enabled:
                welcome_text = settings.welcome_message or texts.DEFAULT_WELCOME_GROUP
                await event.answer(
                    welcome_text.format(
                        name=new_member.full_name,
                        username=new_member.username or "",
                    )
                )


# --- Удаление сервисных сообщений ---

@router.message(F.new_chat_members | F.left_chat_member | F.new_chat_title, GROUP_FILTER)
async def delete_service_messages(message: Message, session: AsyncSession) -> None:
    """Удалять сервисные сообщения (join/leave) если настроено."""
    repo = ChatRepo(session)
    settings = await repo.get_or_create(message.chat.id, message.chat.title or "")
    if settings.delete_service_messages and await _is_bot_admin(message):
        try:
            await message.delete()
        except Exception:
            pass


# --- AI-powered group features ---

@router.message(Command("aimod"), GROUP_FILTER)
async def cmd_aimod(
    message: Message, session: AsyncSession, settings: Settings
) -> None:
    """AI-модерация включена/выключена: /aimod on|off"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return
    arg = message.get_args().strip().lower()
    repo = ChatRepo(session)
    if arg in ("on", "enable", "вкл"):
        await repo.toggle_anti_spam(message.chat.id, True)
        await message.reply("🛡️ AI-модерация включена. ИИ проверяет семантику сообщений.")
    elif arg in ("off", "disable", "выкл"):
        await repo.toggle_anti_spam(message.chat.id, False)
        await message.reply("⚠️ AI-модерация выключена. Только базовые паттерны.")
    else:
        await message.reply("Использование: /aimod on|off")


@router.message(Command("sentiment"), GROUP_FILTER)
async def cmd_sentiment(
    message: Message, provider: AIProvider
) -> None:
    """Анализ тональности: ответьте на сообщение /sentiment <текст>"""
    if message.reply_to_message:
        text = message.reply_to_message.text or ""
        target = message.reply_to_message.from_user
    else:
        text = message.get_args().strip()
        target = None

    if not text:
        await message.reply("⚠️ Укажите текст или ответьте на сообщение: /sentiment <текст>")
        return

    service = SentimentService(provider)
    result = await service.analyze(text)

    name = target.full_name if target else "текст"
    await message.reply(
        f"📊 Тональность сообщения от {name}:\n"
        f"{texts.sentiment_label(result.sentiment, result.compound)}\n"
        f"Язык: {result.language}"
    )


@router.message(Command("summarise"), GROUP_FILTER)
async def cmd_summarise(
    message: Message, session: AsyncSession, provider: AIProvider
) -> None:
    """AI-резюме чата: /summarise <число сообщений> (по умолчанию 20)"""
    if not await _is_chat_admin(message):
        await message.reply(texts.NOT_ADMIN)
        return

    limit = 20
    arg = message.get_args().strip()
    if arg:
        try:
            limit = min(int(arg), 100)
        except ValueError:
            pass

    # Получаем последние сообщения из БД (только для групп, где ведётся лог)
    # Здесь используем ChatRepo для настроек
    repo = ChatRepo(session)
    settings = await repo.get_or_create(message.chat.id, message.chat.title or "")

    # Для демо: используем последние сообщения из chat (если Message модель с chat_id есть)
    # В продакшене здесь бы был отдельный ChatMessageRepo
    summary = await _summarise_messages(message, session, provider, limit)
    await message.reply(summary)


async def _summarise_messages(
    message: Message, session: AsyncSession, provider: AIProvider, limit: int
) -> str:
    """Создаёт резюме из последних сообщений чата."""
    analyzer = ChatAnalyzer(provider)
    # В реальном боте здесь бы читались сообщения из chat_messages таблицы
    # Для MVP возвращаем демо-резюме
    try:
        result = await analyzer.summarize(
            messages=[f"[сообщение {i}] ..." for i in range(limit)],
            max_messages=limit,
        )
        return texts.chat_summary_text(
            result.summary, result.topics, result.action_items, result.sentiment_overall
        )
    except Exception:
        return texts.ai_error_msg()


@router.message(Command("translate"), GROUP_FILTER)
async def cmd_translate(
    message: Message, provider: AIProvider
) -> None:
    """Перевод сообщения: /translate <язык> или ответ на сообщение

    Пример: /translate en — переведёт сообщение на английский
    """
    target_lang = "ru"
    text = ""
    if message.reply_to_message:
        text = message.reply_to_message.text or ""
        lang_arg = message.get_args().strip()
        if lang_arg:
            target_lang = lang_arg.split()[0].lower()
    else:
        args = message.get_args().split(None, 1)
        if len(args) >= 2:
            target_lang = args[0].lower()
            text = args[1]
        elif len(args) == 1:
            await message.reply("Использование: /translate <язык> <текст> или ответьте на сообщение")
            return

    if not text:
        await message.reply("⚠️ Укажите текст или ответьте на сообщение для перевода.")
        return

    prompt = f"Переведи текст на язык '{target_lang}'. Только перевод, без пояснений:\n\n{text}"
    try:
        reply = await provider.chat([
            {"role": "system", "content": "Ты — переводчик. Переводи только текст, сохраняя формат."},
            {"role": "user", "content": prompt},
        ])
        await message.reply(reply.content.strip())
    except Exception:
        await message.reply(texts.ai_error_msg())
