"""
Хендлер: /start, /help — точка входа пользователя.
"""
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from keyboards.keyboards import main_menu

router = Router()

WELCOME_TEXT = """
👋 <b>Привет! Я твой личный финансовый трекер.</b>

Я помогу тебе:
• 💰 Записывать доходы и расходы
• 📊 Смотреть аналитику по периодам
• 📋 Вести историю операций
• 📥 Экспортировать данные в CSV

<b>Как пользоваться:</b>
➕ <b>Доход</b> — записать поступление денег
➖ <b>Расход</b> — записать трату
📊 <b>Аналитика</b> — статистика и сводки
📋 <b>История</b> — последние операции
⚙️ <b>Настройки</b> — управление категориями
"""

HELP_TEXT = """
📖 <b>Справка по боту</b>

<b>Команды:</b>
/start — главное меню
/help  — эта справка

<b>Как добавить расход:</b>
1. Нажми ➖ <b>Расход</b>
2. Выбери категорию
3. Введи сумму (например: <code>1500</code>)
4. Добавь комментарий (необязательно)
5. Подтверди операцию

<b>Форматы суммы:</b>
<code>1500</code> — просто число
<code>1500.50</code> — с копейками
<code>1 500</code> — с пробелом

<b>Аналитика</b> доступна за периоды:
Сегодня / 7 дней / Месяц / Год / Всё время
"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)
