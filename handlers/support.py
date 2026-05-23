from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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

@router.message(F.text == "💬 Поддержка")
async def support_handler(message: types.Message):
    await message.answer(
        "💬 **Поддержка Moon Data 2.0**\n\n"
        "Свяжитесь с нашим специалистом:\n"
        "👉 @meskatov\n\n"
        "По вопросам работы бота, поиска и сотрудничества.",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )