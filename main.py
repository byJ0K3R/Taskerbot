"""
💰 Finance Tracker Bot — точка входа
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from models.database import init_db
from handlers import start, transactions, analytics, admin
from middlewares.auth import AdminOnlyMiddleware
from middlewares.throttle import ThrottleMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    config = Config()

    await init_db()
    logger.info("✅ База данных инициализирована")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(ThrottleMiddleware(rate_limit=1.0))

    # Routers
    dp.include_router(start.router)
    dp.include_router(transactions.router)
    dp.include_router(analytics.router)
    dp.include_router(admin.router)

    logger.info("🚀 Бот запущен")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
