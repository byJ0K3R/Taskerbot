"""
Конфигурация бота — все настройки из переменных окружения (.env)
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    DB_PATH: str = os.getenv("DB_PATH", "finance.db")

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не задан в .env файле!")
        if not self.ADMIN_ID:
            raise ValueError("❌ ADMIN_ID не задан в .env файле!")
