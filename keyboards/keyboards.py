"""
Все клавиатуры бота — inline и reply.
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from services.transaction_service import Category


# ─── ГЛАВНОЕ МЕНЮ ────────────────────────────────────────────────────────────

def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="➕ Доход")
    kb.button(text="➖ Расход")
    kb.button(text="📊 Аналитика")
    kb.button(text="📋 История")
    kb.button(text="⚙️ Настройки")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


# ─── ВЫБОР КАТЕГОРИИ ─────────────────────────────────────────────────────────

def categories_keyboard(categories: list[Category], tx_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat.emoji} {cat.name}",
            callback_data=f"cat:{tx_type}:{cat.id}:{cat.name}",
        )
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


# ─── ПОДТВЕРЖДЕНИЕ ТРАНЗАКЦИИ ─────────────────────────────────────────────────

def confirm_transaction_keyboard(tx_type: str, amount: float,
                                  cat_id: int, comment: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm:{tx_type}:{amount}:{cat_id}:{comment[:20]}",
    )
    builder.button(text="✏️ Изменить", callback_data=f"edit:{tx_type}")
    builder.button(text="❌ Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


# ─── АНАЛИТИКА — ВЫБОР ПЕРИОДА ───────────────────────────────────────────────

def period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    periods = [
        ("Сегодня",     "today"),
        ("7 дней",      "week"),
        ("Этот месяц",  "month"),
        ("Этот год",    "year"),
        ("Всё время",   "all"),
    ]
    for label, period in periods:
        builder.button(text=label, callback_data=f"period:{period}")
    builder.button(text="📥 Экспорт CSV", callback_data="export_csv")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


# ─── ИСТОРИЯ — НАВИГАЦИЯ ─────────────────────────────────────────────────────

def history_keyboard(has_transactions: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_transactions:
        builder.button(text="🗑 Удалить последнюю", callback_data="delete_last")
    builder.button(text="📥 Экспорт CSV", callback_data="export_csv")
    builder.adjust(1)
    return builder.as_markup()


# ─── НАСТРОЙКИ ───────────────────────────────────────────────────────────────

def settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 Категории расходов", callback_data="settings:categories:expense")
    builder.button(text="📂 Категории доходов",  callback_data="settings:categories:income")
    builder.button(text="➕ Добавить категорию", callback_data="settings:add_category")
    builder.adjust(1)
    return builder.as_markup()


def categories_manage_keyboard(categories: list[Category], cat_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"🗑 {cat.emoji} {cat.name}",
            callback_data=f"del_cat:{cat.id}",
        )
    builder.button(text="◀️ Назад", callback_data="back_to_settings")
    builder.adjust(1)
    return builder.as_markup()


# ─── КНОПКА ОТМЕНЫ ───────────────────────────────────────────────────────────

def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel")
    return builder.as_markup()
