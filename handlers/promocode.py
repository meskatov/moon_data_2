from aiogram import Router, types
from aiogram.filters import Command  # <-- ИСПРАВЛЕНО
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

PROMOCODES = {
    "MOON2024": 50,
    "WELCOME": 25
}


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Искать")],
            [KeyboardButton(text="👤 Профиль | 🎫 Промокод")],
            [KeyboardButton(text="🛠️ Административная панель"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )


@router.message(Command("promo"))
async def apply_promocode(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /promo КОД")
        return

    code = args[1].upper()
    if code in PROMOCODES:
        await message.answer(f"✅ Промокод {code} активирован! +{PROMOCODES[code]} баллов.",
                             reply_markup=get_main_menu())
    else:
        await message.answer(f"❌ Промокод {code} недействителен.", reply_markup=get_main_menu())