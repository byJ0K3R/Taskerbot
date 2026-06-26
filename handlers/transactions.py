"""
Хендлер транзакций: добавление дохода и расхода через FSM.
Сценарий:
  1. Пользователь нажимает "Доход" / "Расход"
  2. Бот показывает список категорий (inline-кнопки)
  3. Пользователь выбирает категорию
  4. Бот просит ввести сумму
  5. (Опционально) Пользователь вводит комментарий
  6. Подтверждение → запись в БД
"""
import logging
import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from keyboards.keyboards import (
    categories_keyboard, confirm_transaction_keyboard,
    cancel_keyboard, main_menu,
)
from services.transaction_service import get_categories, add_transaction

logger = logging.getLogger(__name__)
router = Router()


class AddTransaction(StatesGroup):
    choosing_category = State()
    entering_amount   = State()
    entering_comment  = State()
    confirming        = State()


def parse_amount(text: str) -> float | None:
    """Парсит сумму из текста. Поддерживает: 1500, 1500.50, 1 500"""
    cleaned = re.sub(r"[\s_]", "", text.replace(",", "."))
    try:
        val = float(cleaned)
        return val if val > 0 else None
    except ValueError:
        return None


# ─── СТАРТ ДОБАВЛЕНИЯ ────────────────────────────────────────────────────────

@router.message(F.text == "➕ Доход")
async def start_income(message: Message, state: FSMContext):
    await _start_transaction(message, state, "income")


@router.message(F.text == "➖ Расход")
async def start_expense(message: Message, state: FSMContext):
    await _start_transaction(message, state, "expense")


async def _start_transaction(message: Message, state: FSMContext, tx_type: str):
    categories = await get_categories(tx_type)
    if not categories:
        await message.answer("⚠️ Нет категорий. Добавь их в ⚙️ Настройках.")
        return

    label = "дохода" if tx_type == "income" else "расхода"
    await message.answer(
        f"📂 Выбери категорию <b>{label}</b>:",
        reply_markup=categories_keyboard(categories, tx_type),
    )
    await state.set_state(AddTransaction.choosing_category)
    await state.update_data(tx_type=tx_type)


# ─── ВЫБОР КАТЕГОРИИ ─────────────────────────────────────────────────────────

@router.callback_query(AddTransaction.choosing_category, F.data.startswith("cat:"))
async def category_chosen(callback: CallbackQuery, state: FSMContext):
    # Формат: cat:{type}:{id}:{name}
    _, tx_type, cat_id, *name_parts = callback.data.split(":")
    cat_name = ":".join(name_parts)

    await state.update_data(category_id=int(cat_id), category_name=cat_name)
    await state.set_state(AddTransaction.entering_amount)

    await callback.message.edit_text(
        f"✅ Категория: <b>{cat_name}</b>\n\n"
        f"💵 Введи сумму (например: <code>1500</code> или <code>250.50</code>):",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


# ─── ВВОД СУММЫ ──────────────────────────────────────────────────────────────

@router.message(AddTransaction.entering_amount)
async def amount_entered(message: Message, state: FSMContext):
    amount = parse_amount(message.text or "")
    if amount is None:
        await message.answer(
            "❌ Некорректная сумма. Введи число больше нуля.\n"
            "Например: <code>1500</code> или <code>250.50</code>",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(amount=amount)
    await state.set_state(AddTransaction.entering_comment)

    await message.answer(
        f"💵 Сумма: <b>{amount:,.2f} ₽</b>\n\n"
        "✏️ Добавь комментарий (или отправь <code>-</code> чтобы пропустить):",
        reply_markup=cancel_keyboard(),
    )


# ─── ВВОД КОММЕНТАРИЯ ────────────────────────────────────────────────────────

@router.message(AddTransaction.entering_comment)
async def comment_entered(message: Message, state: FSMContext):
    comment = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    # Защита от слишком длинного комментария
    comment = comment[:200]

    data = await state.get_data()
    tx_type = data["tx_type"]
    amount = data["amount"]
    cat_id = data["category_id"]
    cat_name = data["category_name"]

    emoji = "💵" if tx_type == "income" else "💸"
    type_label = "Доход" if tx_type == "income" else "Расход"

    summary = (
        f"{emoji} <b>{type_label}</b>\n"
        f"📂 Категория: <b>{cat_name}</b>\n"
        f"💰 Сумма: <b>{amount:,.2f} ₽</b>\n"
    )
    if comment:
        summary += f"💬 Комментарий: {comment}\n"

    summary += "\nВсё верно?"

    await state.update_data(comment=comment)
    await state.set_state(AddTransaction.confirming)

    await message.answer(
        summary,
        reply_markup=confirm_transaction_keyboard(tx_type, amount, cat_id, comment),
    )


# ─── ПОДТВЕРЖДЕНИЕ ───────────────────────────────────────────────────────────

@router.callback_query(AddTransaction.confirming, F.data.startswith("confirm:"))
async def confirm_transaction(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    tx_id = await add_transaction(
        tx_type=data["tx_type"],
        amount=data["amount"],
        category_id=data["category_id"],
        comment=data.get("comment", ""),
    )

    emoji = "✅💵" if data["tx_type"] == "income" else "✅💸"
    type_label = "Доход" if data["tx_type"] == "income" else "Расход"

    await callback.message.edit_text(
        f"{emoji} <b>{type_label} записан!</b>\n"
        f"📂 {data['category_name']}: <b>{data['amount']:,.2f} ₽</b>\n"
        f"🔖 ID операции: #{tx_id}"
    )
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await state.clear()
    await callback.answer("Записано!")
    logger.info(f"Transaction #{tx_id} added: {data['tx_type']} {data['amount']}")


# ─── РЕДАКТИРОВАНИЕ (начать заново) ─────────────────────────────────────────

@router.callback_query(F.data.startswith("edit:"))
async def edit_transaction(callback: CallbackQuery, state: FSMContext):
    tx_type = callback.data.split(":")[1]
    await state.clear()
    categories = await get_categories(tx_type)
    label = "дохода" if tx_type == "income" else "расхода"
    await callback.message.edit_text(
        f"📂 Выбери категорию <b>{label}</b> заново:",
        reply_markup=categories_keyboard(categories, tx_type),
    )
    await state.set_state(AddTransaction.choosing_category)
    await state.update_data(tx_type=tx_type)
    await callback.answer()


# ─── ОТМЕНА ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
    await callback.answer()
