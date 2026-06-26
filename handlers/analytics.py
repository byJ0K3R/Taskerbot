"""
Хендлер аналитики и истории операций.
"""
import io
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from keyboards.keyboards import period_keyboard, history_keyboard, main_menu
from services.transaction_service import (
    get_summary, get_recent_transactions, get_monthly_chart_data,
    delete_transaction, export_to_csv,
)

logger = logging.getLogger(__name__)
router = Router()

PERIOD_LABELS = {
    "today": "Сегодня",
    "week":  "За 7 дней",
    "month": "За этот месяц",
    "year":  "За этот год",
    "all":   "За всё время",
}


def format_summary(data: dict, period_label: str) -> str:
    """Формирует красивый текст аналитики."""
    income  = data["total_income"]
    expense = data["total_expense"]
    balance = data["balance"]

    balance_emoji = "📈" if balance >= 0 else "📉"
    balance_str   = f"+{balance:,.2f}" if balance >= 0 else f"{balance:,.2f}"

    text = (
        f"📊 <b>Аналитика — {period_label}</b>\n\n"
        f"💵 Доходы:  <b>{income:,.2f} ₽</b>\n"
        f"💸 Расходы: <b>{expense:,.2f} ₽</b>\n"
        f"{balance_emoji} Баланс:  <b>{balance_str} ₽</b>\n"
    )

    if data["top_expenses"]:
        text += "\n<b>Топ расходов:</b>\n"
        for item in data["top_expenses"]:
            pct = (item["total"] / expense * 100) if expense > 0 else 0
            text += f"  {item['emoji']} {item['name']}: {item['total']:,.2f} ₽ ({pct:.0f}%)\n"

    if data["top_incomes"]:
        text += "\n<b>Топ доходов:</b>\n"
        for item in data["top_incomes"]:
            text += f"  {item['emoji']} {item['name']}: {item['total']:,.2f} ₽\n"

    if income == 0 and expense == 0:
        text += "\n💡 Пока нет данных за этот период."

    return text


def build_bar(value: float, max_value: float, width: int = 10) -> str:
    """Текстовый бар для графика."""
    if max_value == 0:
        return "░" * width
    filled = int(value / max_value * width)
    return "█" * filled + "░" * (width - filled)


# ─── АНАЛИТИКА ───────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Аналитика")
async def show_analytics(message: Message):
    await message.answer(
        "📊 <b>Аналитика</b>\nВыбери период:",
        reply_markup=period_keyboard(),
    )


@router.callback_query(F.data.startswith("period:"))
async def period_selected(callback: CallbackQuery):
    period = callback.data.split(":")[1]
    data = await get_summary(period)
    label = PERIOD_LABELS.get(period, period)
    text = format_summary(data, label)
    await callback.message.edit_text(text, reply_markup=period_keyboard())
    await callback.answer()


# ─── ИСТОРИЯ ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 История")
async def show_history(message: Message):
    transactions = await get_recent_transactions(limit=15)

    if not transactions:
        await message.answer(
            "📋 История пуста.\nДобавь первую операцию через ➕ или ➖",
            reply_markup=history_keyboard(False),
        )
        return

    lines = ["📋 <b>Последние операции:</b>\n"]
    for tx in transactions:
        emoji = "💵" if tx.type == "income" else "💸"
        sign  = "+" if tx.type == "income" else "-"
        cat   = f"{tx.category_emoji} {tx.category_name}" if tx.category_name else "—"
        date  = tx.created_at[:10]
        comment = f" · {tx.comment}" if tx.comment else ""
        lines.append(
            f"{emoji} <b>{sign}{tx.amount:,.2f} ₽</b> · {cat}{comment} <i>({date})</i>"
        )

    await message.answer(
        "\n".join(lines),
        reply_markup=history_keyboard(True),
    )


@router.callback_query(F.data == "delete_last")
async def delete_last_transaction(callback: CallbackQuery):
    transactions = await get_recent_transactions(limit=1)
    if not transactions:
        await callback.answer("Нет операций для удаления", show_alert=True)
        return

    tx = transactions[0]
    success = await delete_transaction(tx.id)
    if success:
        await callback.answer(f"🗑 Удалено: {tx.amount:,.2f} ₽", show_alert=True)
        await callback.message.edit_text(
            f"🗑 Операция #{tx.id} удалена.\n"
            f"Сумма: {tx.amount:,.2f} ₽ · {tx.category_name or '—'}"
        )
        await callback.message.answer("Главное меню:", reply_markup=main_menu())
    else:
        await callback.answer("❌ Не удалось удалить", show_alert=True)


# ─── ЭКСПОРТ CSV ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "export_csv")
async def export_csv(callback: CallbackQuery):
    await callback.answer("⏳ Подготавливаю файл...")
    csv_data = await export_to_csv()

    if not csv_data.strip():
        await callback.message.answer("📋 Нет данных для экспорта.")
        return

    file = BufferedInputFile(
        csv_data.encode("utf-8-sig"),  # utf-8-sig для корректного открытия в Excel
        filename="finance_export.csv",
    )
    await callback.message.answer_document(
        file,
        caption="📥 <b>Экспорт транзакций</b>\nОткрой в Excel или Google Sheets.",
    )
    logger.info("CSV exported")
