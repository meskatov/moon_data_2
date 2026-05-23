from aiogram import Router, types, F
from aiogram.filters import Command  # <-- ИСПРАВЛЕНО
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import is_user_verified, add_verified_user, send_tech_log
from config import TGK_CHANNEL_ID, TECH_ADMIN_ID, TGK_INVITE_LINK

router = Router()


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Искать")],
            [KeyboardButton(text="👤 Профиль | 🎫 Промокод")],
            [KeyboardButton(text="🛠️ Административная панель"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )


class VerifyState(StatesGroup):
    waiting_check = State()


@router.message(Command("verify"))
async def cmd_verify(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    if is_user_verified(user_id):
        await message.answer("✅ Вы уже верифицированы!", reply_markup=get_main_menu())
        return

    await state.set_state(VerifyState.waiting_check)
    await message.answer(
        "🔐 **Верификация через ТГК**\n\n"
        "Для доступа к боту необходимо подписаться на наш канал:\n"
        f"👉 {TGK_INVITE_LINK}\n\n"
        "После подписки нажмите кнопку ниже.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Перейти в канал", url=TGK_INVITE_LINK)],
                [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_verify")]
            ]
        )
    )


@router.callback_query(F.data == "check_verify")
async def check_verification(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bot = callback.bot

    try:
        member = await bot.get_chat_member(TGK_CHANNEL_ID, user_id)

        if member.status in ["member", "administrator", "creator"]:
            add_verified_user(user_id)
            await callback.message.edit_text("✅ **Верификация пройдена!**")
            await callback.message.answer(
                f"🌙 Добро пожаловать в Moon Data 2.0, {callback.from_user.first_name}!",
                reply_markup=get_main_menu()
            )
            await callback.answer("✅ Доступ разрешен!")
            await send_tech_log(bot, "✅ Новая верификация", f"Пользователь {user_id} прошел верификацию")
        else:
            await callback.answer("❌ Вы не подписаны на канал!", show_alert=True)
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка проверки", show_alert=True)

    await state.clear()


@router.callback_query(F.data == "start_verify")
async def start_verify_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await cmd_verify(callback.message, state)
    await callback.answer()