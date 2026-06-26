"""
Модели БД и инициализация SQLite через aiosqlite
Схема:
  - transactions: все операции (расход/доход)
  - categories: категории (еда, транспорт, зарплата и т.д.)
"""
import aiosqlite
from config import Config

DB_PATH = Config.DB_PATH if hasattr(Config, "DB_PATH") else "finance.db"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS categories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL UNIQUE,
    type      TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
    emoji     TEXT    DEFAULT '💰',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
    amount      REAL    NOT NULL CHECK(amount > 0),
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    comment     TEXT    DEFAULT '',
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_at);
"""

DEFAULT_CATEGORIES = [
    ("Зарплата",      "income",  "💵"),
    ("Фриланс",       "income",  "💻"),
    ("Инвестиции",    "income",  "📈"),
    ("Прочий доход",  "income",  "💰"),
    ("Продукты",      "expense", "🛒"),
    ("Кафе и рестораны", "expense", "☕"),
    ("Транспорт",     "expense", "🚌"),
    ("ЖКХ",           "expense", "🏠"),
    ("Здоровье",      "expense", "💊"),
    ("Одежда",        "expense", "👕"),
    ("Развлечения",   "expense", "🎮"),
    ("Прочие расходы","expense", "📦"),
]


async def get_db() -> aiosqlite.Connection:
    """Возвращает соединение с БД (использовать как контекстный менеджер)."""
    import os
    config = Config()
    return await aiosqlite.connect(config.DB_PATH)


async def init_db():
    """Создаёт таблицы и наполняет дефолтные категории."""
    config = Config()
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        # Добавляем дефолтные категории, если их нет
        for name, cat_type, emoji in DEFAULT_CATEGORIES:
            await db.execute(
                "INSERT OR IGNORE INTO categories (name, type, emoji) VALUES (?, ?, ?)",
                (name, cat_type, emoji),
            )
        await db.commit()

