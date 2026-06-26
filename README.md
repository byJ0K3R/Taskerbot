# 💰 Finance Tracker Bot

Личный Telegram-бот для учёта доходов и расходов.

## Стек технологий
- **Python 3.11+**
- **aiogram 3.x** — асинхронный фреймворк для Telegram Bot API
- **SQLite + aiosqlite** — лёгкая БД, не требует отдельного сервера
- **FSM (Finite State Machine)** — пошаговые диалоги с пользователем

## Структура проекта
```
finance_bot/
├── main.py                  # Точка входа, запуск бота
├── config.py                # Конфигурация из .env
├── requirements.txt         # Зависимости
├── .env.example             # Пример файла с переменными окружения
├── finance_bot.service      # systemd-сервис для VPS
├── backup.sh                # Скрипт резервного копирования
│
├── models/
│   └── database.py          # Инициализация БД, схема таблиц
│
├── services/
│   └── transaction_service.py  # Вся бизнес-логика: CRUD, аналитика, экспорт
│
├── handlers/
│   ├── start.py             # /start, /help
│   ├── transactions.py      # Добавление дохода/расхода (FSM)
│   ├── analytics.py         # Аналитика, история, экспорт CSV
│   └── admin.py             # Настройки, управление категориями, /stats
│
├── keyboards/
│   └── keyboards.py         # Все inline и reply клавиатуры
│
└── middlewares/
    ├── throttle.py          # Антиспам
    └── auth.py              # Авторизация (заглушка)
```

## Схема БД
```sql
categories
  id, name, type (income|expense), emoji, created_at

transactions
  id, type (income|expense), amount, category_id → categories.id,
  comment, created_at
```

---

## 🚀 Запуск локально (на Android через Termux)

```bash
# 1. Установи зависимости
pkg install python git

# 2. Клонируй или скопируй проект
cd ~
# (скопируй папку finance_bot сюда)

# 3. Создай виртуальное окружение
cd finance_bot
python -m venv venv
source venv/bin/activate

# 4. Установи пакеты
pip install -r requirements.txt

# 5. Настрой .env
cp .env.example .env
nano .env
# Вставь BOT_TOKEN и ADMIN_ID

# 6. Запусти
python main.py
```

---

## 🖥 Деплой на VPS (Linux / Ubuntu)

```bash
# 1. Подключись к серверу
ssh ubuntu@YOUR_SERVER_IP

# 2. Установи Python
sudo apt update && sudo apt install python3.11 python3.11-venv git -y

# 3. Скопируй проект
scp -r finance_bot ubuntu@YOUR_SERVER_IP:/home/ubuntu/

# 4. Настрой окружение
cd /home/ubuntu/finance_bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Заполни .env
cp .env.example .env
nano .env

# 6. Настрой systemd-сервис
sudo cp finance_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable finance_bot
sudo systemctl start finance_bot

# Проверить статус:
sudo systemctl status finance_bot

# Смотреть логи в реальном времени:
journalctl -u finance_bot -f
```

---

## 🔄 Обновление бота на сервере

```bash
cd /home/ubuntu/finance_bot
git pull  # если используешь git
sudo systemctl restart finance_bot
```

---

## 💾 Резервное копирование

```bash
# Сделать бэкап вручную:
bash backup.sh

# Автобэкап каждый день в 3:00 через cron:
crontab -e
# Добавь строку:
0 3 * * * /home/ubuntu/finance_bot/backup.sh
```

---

## ⚠️ Возможные ошибки и решения

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `BOT_TOKEN не задан` | Нет .env файла | `cp .env.example .env` и заполни |
| `Conflict: terminated by other getUpdates` | Бот запущен дважды | Останови второй экземпляр |
| `aiosqlite.OperationalError` | БД заблокирована | Перезапусти бота |
| Бот не отвечает | Нет интернета на сервере | Проверь `ping api.telegram.org` |

---

## 📈 Следующие шаги (расширение)

- [ ] Ежемесячный лимит бюджета по категориям
- [ ] Плановые расходы (повторяющиеся операции)
- [ ] Напоминания (вечернее уведомление "не забудь записать расходы")
- [ ] Графики через matplotlib (PNG-диаграммы)
- [ ] Подключение PostgreSQL (при росте данных)
- [ ] Веб-дашборд (FastAPI + простой HTML)
