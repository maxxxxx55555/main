"""/start, /help, /stats — онбординг и статус лимитов."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import main_menu
from app.bot.states import ConfirmStates
from app.config import Settings
from app.db.models.user import User
from app.db.repo.messages import MessageRepo
from app.db.repo.users import UserRepo
from app.services.billing.plans import PlanCatalog
from app.services.limits.usage import UsageService

router = Router(name="start")

WELCOME = (
    "👋 Привет, {name}!\n\n"
    "Я — <b>AI-Сотрудник</b>: отвечаю вашим клиентам 24/7, квалифицирую лидов, "
    "записываю на консультации и не даю потерять ни одну заявку.\n\n"
    "Просто напишите мне вопрос — как будто это тестовый клиент. "
    "А чтобы я отвечал от лица вашего бизнеса, загрузите базу знаний (FAQ, цены, условия) в разделе «📚 База знаний».\n\n"
    "⚠️ <i>Ваши сообщения передаются LLM-провайдеру для генерации ответов.</i>"
)

HELP = (
    "<b>Команды:</b>\n"
    "/start — начать работу\n"
    "/help — эта справка\n"
    "/stats — остаток лимита и тариф\n"
    "/buy — тарифы и оплата (Telegram Stars)\n"
    "/knowledge — база знаний (PRO/Business)\n"
    "/forget_me — удалить все мои данные\n\n"
    "<b>Как это работает:</b> напишите сообщение — я отвечу как AI-ассистент "
    "вашего бизнеса. Лимит бесплатного тарифа обновляется каждые 30 дней."
)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user: User,
    catalog: PlanCatalog,
    session: AsyncSession,
) -> None:
    await UserRepo(session).get_or_create(user.tg_id, user.tz)
    name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        WELCOME.format(name=name),
        reply_markup=main_menu(catalog),
    )


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(event: Message | CallbackQuery) -> None:
    text = HELP
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text)


@router.message(Command("stats"))
async def cmd_stats(
    message: Message, user: User, catalog: PlanCatalog, usage: UsageService, settings: Settings
) -> None:
    limit = catalog.limit_for(user.plan)
    remaining = max(limit - user.messages_used, 0)
    plan = catalog.get(user.plan)
    await message.answer(
        "📊 <b>Ваш статус</b>\n"
        f"Тариф: <b>{plan.title if plan else user.plan}</b>\n"
        f"Лимит: {user.messages_used}/{limit} сообщений использовано\n"
        f"Осталось: <b>{remaining}</b>\n"
        f"Обновление лимита: {user.period_reset_at.strftime('%d.%m.%Y %H:%M UTC')}\n\n"
        "Апгрейд: /buy"
    )


@router.callback_query(F.data == "menu")
async def cb_menu(callback: CallbackQuery, catalog: PlanCatalog, state=None) -> None:
    if state is not None:
        await state.clear()
    if callback.message is not None:
        await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu(catalog))
    await callback.answer()


@router.callback_query(F.data == "forget_me")
async def cb_forget(
    callback: CallbackQuery, session: AsyncSession, user: User, settings: Settings
) -> None:
    from app.bot.keyboards.inline import forget_confirm_kb

    if callback.message is not None:
        await callback.message.edit_text(
            "⚠️ Удалить <b>все</b> ваши данные: профиль, историю диалогов, базу знаний?\n"
            "Действие необратимо.",
            reply_markup=forget_confirm_kb(),
        )
    await callback.answer()


@router.callback_query(F.data == "forget_confirm")
async def cb_forget_confirm(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    from app.db.repo.knowledge import KnowledgeRepo

    await MessageRepo(session).delete_history(user.id)
    await KnowledgeRepo(session).delete_for_owner(user.id)
    await session.delete(user)
    await callback.message.edit_text("🗑 Все ваши данные удалены. Введите /start, чтобы начать заново.")
    await callback.answer()