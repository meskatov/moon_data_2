from aiogram import Router, types, F
from aiogram.filters import Command  # <-- ИСПРАВЛЕНО
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db_manager import is_admin, get_stats, get_all_users, get_all_admins, add_admin, remove_admin, \
    send_tech_log, get_bot_status, set_bot_status
from config import TECH_ADMIN_ID

router = Router()


def get_admin_menu(rank):
    buttons = []
    if rank in ["tech_owner", "owner"]:
        buttons.append([KeyboardButton(text="📊 Статистика")])
        buttons.append([KeyboardButton(text="👥 Список пользователей")])
        buttons.append([KeyboardButton(text="🔌 Управление ботом")])
        buttons.append([KeyboardButton(text="👑 Управление админами")])
    elif rank == "admin":
        buttons.append([KeyboardButton(text="📊 Статистика")])

    buttons.append([KeyboardButton(text="◀️ Главное меню")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Искать")],
            [KeyboardButton(text="👤 Профиль | 🎫 Промокод")],
            [KeyboardButton(text="🛠️ Административная панель"), KeyboardButton(text="💬 Поддержка")]
        ],
        resize_keyboard=True
    )


@router.message(F.text == "🛠️ Административная панель")
async def admin_panel(message: types.Message):
    rank = is_admin(message.from_user.id)
    if not rank:
        await message.answer("⛔ У вас нет доступа.")
        return
    await message.answer(f"⚙️ Админ-панель (ранг: {rank})", reply_markup=get_admin_menu(rank))


@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    stats = get_stats()
    await message.answer(
        f"📈 **Статистика**\n\n👥 Пользователей: {stats['users']}\n🔍 Запросов: {stats['searches']}\n✅ Верифицировано: {stats['verified']}",
        parse_mode="Markdown"
    )


@router.message(F.text == "👥 Список пользователей")
async def list_users(message: types.Message):
    rank = is_admin(message.from_user.id)
    if rank not in ["tech_owner", "owner"]:
        return
    users = get_all_users()
    text = "📋 **Список пользователей:**\n\n"
    for u in users[:20]:
        text += f"• {u[1] or 'NoName'} (ID: {u[0]}) - запросов: {u[4]}\n"
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "👑 Управление админами")
async def manage_admins(message: types.Message):
    rank = is_admin(message.from_user.id)
    if rank not in ["tech_owner", "owner"]:
        return
    admins = get_all_admins()
    text = "👑 **Администраторы:**\n\n"
    for a in admins:
        text += f"• ID {a[0]} - {a[1]}\n"
    text += "\n📝 Команды:\n/addadmin ID ранг\n/removeadmin ID"
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("addadmin"))
async def add_admin_cmd(message: types.Message):
    rank = is_admin(message.from_user.id)
    if rank not in ["tech_owner", "owner"]:
        await message.answer("⛔ Нет прав")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("❌ Использование: /addadmin ID ранг")
        return
    try:
        target_id = int(args[1])
        new_rank = args[2]
        if new_rank not in ["tech_owner", "owner", "admin"]:
            await message.answer("❌ Ранги: tech_owner, owner, admin")
            return
        add_admin(target_id, new_rank, message.from_user.id)
        await message.answer(f"✅ Админ {target_id} добавлен")
    except:
        await message.answer("❌ Ошибка")


@router.message(Command("removeadmin"))
async def remove_admin_cmd(message: types.Message):
    rank = is_admin(message.from_user.id)
    if rank not in ["tech_owner", "owner"]:
        await message.answer("⛔ Нет прав")
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /removeadmin ID")
        return
    try:
        target_id = int(args[1])
        remove_admin(target_id)
        await message.answer(f"✅ Админ {target_id} удален")
    except:
        await message.answer("❌ Ошибка")


@router.message(F.text == "🔌 Управление ботом")
async def manage_bot(message: types.Message):
    rank = is_admin(message.from_user.id)
    if rank not in ["tech_owner", "owner"]:
        return
    current = get_bot_status()
    await message.answer(
        f"⚙️ **Управление ботом**\n\nСтатус: {'🟢 ВКЛЮЧЕН' if current else '🔴 ВЫКЛЮЧЕН'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔴 ВЫКЛЮЧИТЬ" if current else "🟢 ВКЛЮЧИТЬ",
                                      callback_data="bot_off" if current else "bot_on")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
            ]
        )
    )


@router.callback_query(F.data == "bot_off")
async def turn_off(callback: types.CallbackQuery):
    set_bot_status(False)
    await callback.message.edit_text("🔴 Бот выключен")
    await callback.answer()


@router.callback_query(F.data == "bot_on")
async def turn_on(callback: types.CallbackQuery):
    set_bot_status(True)
    await callback.message.edit_text("🟢 Бот включен")
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.delete()
    rank = is_admin(callback.from_user.id)
    await callback.message.answer("⚙️ Админ-панель", reply_markup=get_admin_menu(rank))
    await callback.answer()


@router.message(F.text == "◀️ Главное меню")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_menu())