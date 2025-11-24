#!/bin/bash

# Скрипт для запуска обоих ботов
# Использование: ./start_bots.sh

echo "🚀 Запуск Telegram ботов..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Скопируйте .env.example в .env и заполните все значения."
    exit 1
fi

# Проверка виртуального окружения
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
fi

# Создание папки для логов
mkdir -p logs

# Запуск User Bot в фоне
echo "🤖 Запуск User Bot..."
python3 user_bot.py > logs/user_bot.log 2>&1 &
USER_BOT_PID=$!
echo "User Bot запущен (PID: $USER_BOT_PID)"

# Небольшая задержка
sleep 2

# Запуск Admin Bot в фоне
echo "👨‍💼 Запуск Admin Bot..."
python3 admin_bot.py > logs/admin_bot.log 2>&1 &
ADMIN_BOT_PID=$!
echo "Admin Bot запущен (PID: $ADMIN_BOT_PID)"

echo ""
echo "✅ Оба бота запущены!"
echo "📋 PID процессов:"
echo "   User Bot: $USER_BOT_PID"
echo "   Admin Bot: $ADMIN_BOT_PID"
echo ""
echo "📝 Логи:"
echo "   User Bot: logs/user_bot.log"
echo "   Admin Bot: logs/admin_bot.log"
echo ""
echo "Для остановки ботов используйте:"
echo "   kill $USER_BOT_PID $ADMIN_BOT_PID"
echo ""
echo "Или используйте: ./stop_bots.sh"

# Сохранение PID в файл для остановки
echo "$USER_BOT_PID $ADMIN_BOT_PID" > bots.pid


