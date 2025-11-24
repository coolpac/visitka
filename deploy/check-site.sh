#!/bin/bash

# Скрипт для проверки доступности сайта
# Использование: ./check-site.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}
DOMAIN="annaivaschenko.ru"

echo "🔍 Проверка доступности сайта $DOMAIN"
echo ""

ssh "$SERVER" << ENDSSH
echo "📊 Статус Nginx:"
systemctl status nginx --no-pager -l | head -n 20
echo ""

echo "🔍 Проверка конфигурации Nginx:"
nginx -t
echo ""

echo "📝 Последние ошибки Nginx (20 строк):"
tail -n 20 /var/log/nginx/error.log 2>/dev/null || echo "Логи не найдены"
echo ""

echo "📝 Последние записи access.log (10 строк):"
tail -n 10 /var/log/nginx/access.log 2>/dev/null || echo "Логи не найдены"
echo ""

echo "🌐 Проверка портов:"
netstat -tlnp | grep -E ':(80|443)' || ss -tlnp | grep -E ':(80|443)'
echo ""

echo "📁 Проверка файлов сайта:"
ls -la /var/www/annaivaschenko.ru/ | head -n 10
echo ""

echo "🔐 Проверка SSL сертификата:"
if [ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo "✅ SSL сертификат найден"
    openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -dates 2>/dev/null || echo "Ошибка чтения сертификата"
else
    echo "❌ SSL сертификат не найден"
fi
ENDSSH

echo ""
echo "🌐 Проверка с локальной машины:"
curl -I "https://$DOMAIN" 2>&1 | head -n 10 || echo "Не удалось подключиться"
curl -I "http://$DOMAIN" 2>&1 | head -n 10 || echo "Не удалось подключиться"

