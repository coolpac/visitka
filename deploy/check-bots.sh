#!/bin/bash

# Скрипт для проверки работы ботов
# Использование: ./check-bots.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}

echo "🔍 Проверка работы ботов"
echo ""

ssh "$SERVER" << 'ENDSSH'
echo "📊 Статус сервисов:"
echo ""
systemctl status user-bot.service --no-pager -l
echo ""
systemctl status admin-bot.service --no-pager -l
echo ""

echo "📝 Последние логи User Bot (20 строк):"
echo "---"
tail -n 20 /var/log/annaivaschenko/user-bot.log 2>/dev/null || echo "Логи не найдены"
echo "---"
echo ""

echo "📝 Последние логи Admin Bot (20 строк):"
echo "---"
tail -n 20 /var/log/annaivaschenko/admin-bot.log 2>/dev/null || echo "Логи не найдены"
echo "---"
echo ""

echo "📝 Ошибки User Bot:"
echo "---"
tail -n 10 /var/log/annaivaschenko/user-bot.error.log 2>/dev/null || echo "Ошибок не найдено"
echo "---"
echo ""

echo "📝 Ошибки Admin Bot:"
echo "---"
tail -n 10 /var/log/annaivaschenko/admin-bot.error.log 2>/dev/null || echo "Ошибок не найдено"
echo "---"
echo ""

echo "🔧 Проверка .env файла:"
echo "---"
cd /var/www/annaivaschenko.ru/bots
if [ -f .env ]; then
    echo "✅ Файл .env существует"
    echo "Проверка заполненности:"
    grep -v "^#" .env | grep -v "^$" | grep "your_" && echo "⚠️  Обнаружены незаполненные поля!" || echo "✅ Все поля заполнены"
else
    echo "❌ Файл .env не найден!"
fi
echo "---"
ENDSSH

