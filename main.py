import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command  # <-- ИСПРАВЛЕНО
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from config import TOKEN, OWNER_ID, TECH_ADMIN_ID, TGK_INVITE_LINK
from database.db_manager import init_db, add_user, is_admin, send_tech_log, is_user_verified, get_bot_status, \
    add_verified_user
from handlers import search, profile, promocode, admin, support, verification

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

os.makedirs("data", exist_ok=True)


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Искать")],
            [KeyboardButton(text="👤 Профиль | 🎫 Промокод")],
            [KeyboardButton(text="🛠️ Административная панель"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )


class AccessMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        admin_rank = is_admin(user_id)

        allowed = ["/start", "/verify", "/help"]
        if event.text and any(event.text.startswith(cmd) for cmd in allowed):
            return await handler(event, data)

        if admin_rank:
            if not get_bot_status() and admin_rank not in ["tech_owner", "owner"]:
                await event.answer("⛔ Бот временно отключен")
                return
            return await handler(event, data)

        if not is_user_verified(user_id):
            await event.answer(
                f"🔐 **Требуется верификация!**\n\n"
                f"Подпишитесь на канал: {TGK_INVITE_LINK}\n"
                f"После подписки введите /verify",
                parse_mode="Markdown"
            )
            return

        if not get_bot_status():
            await event.answer("⛔ Бот временно отключен")
            return

        return await handler(event, data)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user

    if not is_user_verified(user.id):
        await message.answer(
            f"🌙 **Moon Data 2.0**\n\n"
            f"Привет, {user.first_name}!\n\n"
            f"🔐 Для доступа к боту верифицируйтесь через /verify",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Верификация", callback_data="start_verify")]
                ]
            )
        )
        return

    add_user(user.id, user.username, user.first_name, user.last_name)
    await message.answer(f"🌙 Добро пожаловать в Moon Data 2.0!", reply_markup=get_main_menu())


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 **Помощь**\n\n"
        "🔍 Искать - поиск информации\n"
        "👤 Профиль - ваша статистика\n"
        "💬 Поддержка - @meskatov\n\n"
        f"📢 Канал: {TGK_INVITE_LINK}",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )


# Регистрация
dp.include_router(verification.router)
dp.include_router(search.router)
dp.include_router(profile.router)
dp.include_router(promocode.router)
dp.include_router(admin.router)
dp.include_router(support.router)

dp.message.middleware(AccessMiddleware())


async def main():
    init_db()

    if not is_admin(OWNER_ID):
        from database.db_manager import add_admin
        add_admin(OWNER_ID, "tech_owner", OWNER_ID)

    if TECH_ADMIN_ID != OWNER_ID and not is_admin(TECH_ADMIN_ID):
        from database.db_manager import add_admin
        add_admin(TECH_ADMIN_ID, "tech_owner", OWNER_ID)

    for aid in [OWNER_ID, TECH_ADMIN_ID]:
        if not is_user_verified(aid):
            add_verified_user(aid)

    print("🚀 Moon Data 2.0 запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())