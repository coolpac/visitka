#!/bin/bash

# Скрипт для создания .env файла на сервере
# Использование: ./create-env-on-server.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}
REMOTE_DIR="/var/www/annaivaschenko.ru/bots"

echo "📝 Создание .env файла на сервере"
echo "Сервер: $SERVER"
echo ""

# Копируем .env.example на сервер
echo "📦 Копирование .env.example на сервер..."
scp "$(dirname "$0")/../bots/.env.example" "$SERVER:$REMOTE_DIR/.env"

echo ""
echo "✅ Файл .env создан на сервере!"
echo ""
echo "Теперь отредактируйте его:"
echo "  ssh $SERVER"
echo "  nano $REMOTE_DIR/.env"
echo ""
echo "Или используйте команду ниже для автоматического редактирования:"
echo "  ssh $SERVER 'nano $REMOTE_DIR/.env'"

