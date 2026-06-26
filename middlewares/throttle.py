"""
Middleware антиспама — ограничивает частоту сообщений.
"""
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        """rate_limit — минимальный интервал между сообщениями в секундах."""
        self.rate_limit = rate_limit
        self._user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if user_id:
            now = time.monotonic()
            last = self._user_timestamps.get(user_id, 0)
            if now - last < self.rate_limit:
                await event.answer("⏳ Не так быстро! Подожди секунду.")
                return
            self._user_timestamps[user_id] = now

        return await handler(event, data)
