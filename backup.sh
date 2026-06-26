#!/bin/bash
# backup.sh — резервное копирование БД
# Добавь в cron: 0 3 * * * /home/ubuntu/finance_bot/backup.sh

BACKUP_DIR="/home/ubuntu/backups/finance_bot"
DB_FILE="/home/ubuntu/finance_bot/finance.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Копируем БД
cp "$DB_FILE" "$BACKUP_DIR/finance_$DATE.db"

# Удаляем бэкапы старше 30 дней
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete

echo "✅ Бэкап создан: finance_$DATE.db"
