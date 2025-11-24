#!/bin/bash

# Скрипт для исправления конфигурации Nginx с SSL
# Использование: ./fix-nginx-ssl.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}

echo "🔧 Исправление конфигурации Nginx с SSL"
echo ""

scp "$(dirname "$0")/nginx.conf" "$SERVER:/tmp/annaivaschenko.ru.conf"

ssh "$SERVER" << 'ENDSSH'
echo "📝 Обновление конфигурации Nginx..."
sudo mv /tmp/annaivaschenko.ru.conf /etc/nginx/sites-available/annaivaschenko.ru
sudo ln -sf /etc/nginx/sites-available/annaivaschenko.ru /etc/nginx/sites-enabled/

echo "🔍 Проверка конфигурации..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    echo "🔄 Перезагрузка Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx перезагружен"
else
    echo "❌ Ошибка в конфигурации Nginx"
    exit 1
fi

echo ""
echo "📊 Статус Nginx:"
sudo systemctl status nginx --no-pager | head -n 10
ENDSSH

echo ""
echo "✅ Готово! Проверьте сайт:"
echo "  https://annaivaschenko.ru"
echo "  https://www.annaivaschenko.ru"

