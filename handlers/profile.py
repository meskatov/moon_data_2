from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.db_manager import get_user_profile, get_user_history

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


@router.message(F.text == "👤 Профиль | 🎫 Промокод")
async def profile_menu(message: types.Message):
    user_id = message.from_user.id
    user = get_user_profile(user_id)
    history = get_user_history(user_id, 5)

    history_text = "\n".join([f"• {h[0]}: {h[1][:30]}..." for h in history]) if history else "Нет запросов"

    profile_text = f"""
👤 **Профиль Moon Data 2.0**

**Никнейм:** {user[2] if user else message.from_user.first_name}
**Юзер:** @{message.from_user.username}
**Айди:** `{user_id}`
**Дата прихода:** {user[5] if user else 'Неизвестно'}

📊 **Статистика:**
• Всего запросов: {user[6] if user else 0}

📜 **Последние запросы:**
{history_text}

🎫 Промокоды в разработке
    """
    await message.answer(profile_text, reply_markup=get_main_menu(), parse_mode="Markdown")