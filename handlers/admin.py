"""
Хендлер настроек и админ-панели.
Управление категориями (добавить / удалить).
"""
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import Config
from keyboards.keyboards import (
    settings_keyboard, categories_manage_keyboard,
    cancel_keyboard, main_menu,
)
from services.transaction_service import (
    get_categories, add_category, delete_category,
)

logger = logging.getLogger(__name__)
router = Router()
config = Config()


class AddCategory(StatesGroup):
    choosing_type = State()
    entering_name = State()
    entering_emoji = State()


# ─── НАСТРОЙКИ ───────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    await message.answer(
        "⚙️ <b>Настройки</b>\n\nУправление категориями:",
        reply_markup=settings_keyboard(),
    )


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\nУправление категориями:",
        reply_markup=settings_keyboard(),
    )
    await callback.answer()


# ─── ПРОСМОТР КАТЕГОРИЙ ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("settings:categories:"))
async def show_categories(callback: CallbackQuery):
    cat_type = callback.data.split(":")[2]
    categories = await get_categories(cat_type)
    label = "расходов" if cat_type == "expense" else "доходов"

    if not categories:
        await callback.message.edit_text(
            f"📂 Категории <b>{label}</b> пусты.\n\nНажми «Добавить категорию».",
            reply_markup=settings_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📂 <b>Категории {label}</b>\nНажми на категорию чтобы удалить:",
        reply_markup=categories_manage_keyboard(categories, cat_type),
    )
    await callback.answer()


# ─── УДАЛЕНИЕ КАТЕГОРИИ ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("del_cat:"))
async def delete_category_handler(callback: CallbackQuery):
    cat_id = int(callback.data.split(":")[1])
    success = await delete_category(cat_id)
    if success:
        await callback.answer("🗑 Категория удалена", show_alert=True)
        await callback.message.edit_text(
            "✅ Категория удалена.\n\nВернись в настройки:",
            reply_markup=settings_keyboard(),
        )
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)


# ─── ДОБАВЛЕНИЕ КАТЕГОРИИ ─────────────────────────────────────────────────────

@router.callback_query(F.data == "settings:add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.button(text="💸 Расход", callback_data="newcat_type:expense")
    builder.button(text="💵 Доход",  callback_data="newcat_type:income")
    builder.button(text="❌ Отмена", callback_data="cancel_settings")
    builder.adjust(2, 1)

    await callback.message.edit_text(
        "➕ <b>Новая категория</b>\nВыбери тип:",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(AddCategory.choosing_type)
    await callback.answer()


@router.callback_query(AddCategory.choosing_type, F.data.startswith("newcat_type:"))
async def category_type_chosen(callback: CallbackQuery, state: FSMContext):
    cat_type = callback.data.split(":")[1]
    await state.update_data(cat_type=cat_type)
    await state.set_state(AddCategory.entering_name)
    await callback.message.edit_text(
        "✏️ Введи <b>название</b> новой категории:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddCategory.entering_name)
async def category_name_entered(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer(
            "❌ Название должно быть от 2 до 50 символов.",
            reply_markup=cancel_keyboard(),
        )
        return
    await state.update_data(name=name)
    await state.set_state(AddCategory.entering_emoji)
    await message.answer(
        f"Название: <b>{name}</b>\n\n"
        "Введи <b>эмодзи</b> для категории (например: 🍕 🚗 💊)\n"
        "Или отправь <code>-</code> чтобы использовать 💰",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddCategory.entering_emoji)
async def category_emoji_entered(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    emoji = "💰" if text == "-" else text[0] if text else "💰"

    data = await state.get_data()
    success = await add_category(data["name"], data["cat_type"], emoji)

    if success:
        type_label = "расход" if data["cat_type"] == "expense" else "доход"
        await message.answer(
            f"✅ Категория добавлена!\n{emoji} <b>{data['name']}</b> ({type_label})",
            reply_markup=main_menu(),
        )
        logger.info(f"Category added: {data['name']} ({data['cat_type']})")
    else:
        await message.answer(
            f"⚠️ Категория <b>{data['name']}</b> уже существует.",
            reply_markup=main_menu(),
        )
    await state.clear()


# ─── ОТМЕНА В НАСТРОЙКАХ ─────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel_settings")
async def cancel_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=settings_keyboard(),
    )
    await callback.answer()


# ─── ADMIN: статистика ────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id != config.ADMIN_ID:
        return

    from services.transaction_service import get_summary
    data = await get_summary("all")

    await message.answer(
        f"🔐 <b>Статистика (все время)</b>\n\n"
        f"💵 Всего доходов:  {data['total_income']:,.2f} ₽\n"
        f"💸 Всего расходов: {data['total_expense']:,.2f} ₽\n"
        f"📊 Баланс:         {data['balance']:,.2f} ₽"
    )
