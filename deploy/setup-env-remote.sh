#!/bin/bash

# Скрипт для настройки .env файла на сервере через SSH
# Использование: ./setup-env-remote.sh

SERVER="root@81.200.153.155"
REMOTE_DIR="/var/www/annaivaschenko.ru/bots"

echo "🔧 Настройка .env файла на сервере"
echo ""

# Создаем .env из примера если его нет
ssh "$SERVER" << 'ENDSSH'
cd /var/www/annaivaschenko.ru/bots

if [ ! -f .env ]; then
    echo "📝 Создание .env из .env.example..."
    cp .env.example .env
    echo "✅ Файл .env создан"
else
    echo "⚠️  Файл .env уже существует"
fi

echo ""
echo "📋 Текущее содержимое .env:"
echo "---"
cat .env | head -20
echo "---"
echo ""
echo "Для редактирования выполните:"
echo "  nano /var/www/annaivaschenko.ru/bots/.env"
echo ""
echo "После редактирования перезапустите боты:"
echo "  systemctl restart user-bot.service"
echo "  systemctl restart admin-bot.service"
ENDSSH

