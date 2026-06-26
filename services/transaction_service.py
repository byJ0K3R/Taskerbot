"""
Сервис транзакций — вся бизнес-логика работы с БД.
Здесь только чистые async-функции, никакой логики бота.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiosqlite
from models.database import get_db


@dataclass
class Transaction:
    id: int
    type: str          # 'income' | 'expense'
    amount: float
    category_id: Optional[int]
    category_name: Optional[str]
    category_emoji: Optional[str]
    comment: str
    created_at: str


@dataclass
class Category:
    id: int
    name: str
    type: str
    emoji: str


# ─── КАТЕГОРИИ ───────────────────────────────────────────────────────────────

async def get_categories(cat_type: str) -> list[Category]:
    """Все категории по типу (income / expense)."""
    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, type, emoji FROM categories WHERE type = ? ORDER BY name",
            (cat_type,),
        )
        rows = await cursor.fetchall()
        return [Category(**dict(r)) for r in rows]


async def add_category(name: str, cat_type: str, emoji: str = "💰") -> bool:
    """Добавить новую категорию. Возвращает False, если уже существует."""
    try:
        async with await get_db() as db:
            await db.execute(
                "INSERT INTO categories (name, type, emoji) VALUES (?, ?, ?)",
                (name.strip(), cat_type, emoji),
            )
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def delete_category(category_id: int) -> bool:
    """Удалить категорию (транзакции не удаляются, category_id станет NULL)."""
    async with await get_db() as db:
        cursor = await db.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


# ─── ТРАНЗАКЦИИ ──────────────────────────────────────────────────────────────

async def add_transaction(
    tx_type: str,
    amount: float,
    category_id: int,
    comment: str = "",
) -> int:
    """Добавить транзакцию. Возвращает её id."""
    async with await get_db() as db:
        cursor = await db.execute(
            """INSERT INTO transactions (type, amount, category_id, comment)
               VALUES (?, ?, ?, ?)""",
            (tx_type, amount, category_id, comment.strip()),
        )
        await db.commit()
        return cursor.lastrowid


async def delete_transaction(tx_id: int) -> bool:
    """Удалить транзакцию по id."""
    async with await get_db() as db:
        cursor = await db.execute(
            "DELETE FROM transactions WHERE id = ?", (tx_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_recent_transactions(limit: int = 10) -> list[Transaction]:
    """Последние N транзакций."""
    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT t.id, t.type, t.amount, t.category_id,
                      c.name AS category_name, c.emoji AS category_emoji,
                      t.comment, t.created_at
               FROM transactions t
               LEFT JOIN categories c ON t.category_id = c.id
               ORDER BY t.created_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [Transaction(**dict(r)) for r in rows]


# ─── АНАЛИТИКА ───────────────────────────────────────────────────────────────

async def get_summary(period: str = "month") -> dict:
    """
    Сводка за период: 'today', 'week', 'month', 'year', 'all'.
    Возвращает total_income, total_expense, balance, по категориям.
    """
    period_filter = {
        "today": "DATE(created_at) = DATE('now')",
        "week":  "created_at >= DATE('now', '-7 days')",
        "month": "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')",
        "year":  "strftime('%Y', created_at) = strftime('%Y', 'now')",
        "all":   "1=1",
    }.get(period, "1=1")

    async with await get_db() as db:
        db.row_factory = aiosqlite.Row

        # Итоги
        cursor = await db.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS total_expense
            FROM transactions
            WHERE {period_filter}
        """)
        totals = dict(await cursor.fetchone())
        totals["balance"] = totals["total_income"] - totals["total_expense"]

        # Топ категорий расходов
        cursor = await db.execute(f"""
            SELECT c.emoji, c.name, SUM(t.amount) AS total
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'expense' AND {period_filter}
            GROUP BY t.category_id
            ORDER BY total DESC
            LIMIT 5
        """)
        totals["top_expenses"] = [dict(r) for r in await cursor.fetchall()]

        # Топ категорий доходов
        cursor = await db.execute(f"""
            SELECT c.emoji, c.name, SUM(t.amount) AS total
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'income' AND {period_filter}
            GROUP BY t.category_id
            ORDER BY total DESC
            LIMIT 5
        """)
        totals["top_incomes"] = [dict(r) for r in await cursor.fetchall()]

        return totals


async def get_monthly_chart_data() -> list[dict]:
    """Данные по месяцам за последний год (для текстового графика)."""
    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT
                strftime('%Y-%m', created_at) AS month,
                SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            WHERE created_at >= DATE('now', '-12 months')
            GROUP BY month
            ORDER BY month
        """)
        return [dict(r) for r in await cursor.fetchall()]


async def export_to_csv() -> str:
    """Экспортирует все транзакции в CSV-строку."""
    import csv
    import io

    async with await get_db() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT t.id, t.type, t.amount, c.name AS category, t.comment, t.created_at
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            ORDER BY t.created_at DESC
        """)
        rows = await cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Тип", "Сумма", "Категория", "Комментарий", "Дата"])
    for r in rows:
        tx_type = "Доход" if r["type"] == "income" else "Расход"
        writer.writerow([r["id"], tx_type, r["amount"],
                         r["category"] or "—", r["comment"], r["created_at"]])
    return output.getvalue()
