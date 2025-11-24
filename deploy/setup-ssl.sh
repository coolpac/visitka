#!/bin/bash

# Скрипт для получения SSL сертификата
# Использование: ./setup-ssl.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}
DOMAIN="annaivaschenko.ru"
EMAIL="${2:-}"  # Email можно передать вторым параметром

echo "🔒 Настройка SSL сертификата для $DOMAIN"
echo ""

# Если email не указан, запрашиваем
if [ -z "$EMAIL" ]; then
    read -p "Введите ваш email для Let's Encrypt: " EMAIL
fi

ssh "$SERVER" << ENDSSH
DOMAIN="$DOMAIN"
EMAIL="$EMAIL"

echo "🔍 Проверка DNS..."
# Получаем IPv4 адрес домена
DOMAIN_IP=\$(dig +short \$DOMAIN A | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\$' | head -n1)
# Получаем IPv4 адрес сервера
SERVER_IP=\$(hostname -I | awk '{print \$1}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\$' | head -n1)

if [ -z "\$SERVER_IP" ]; then
    SERVER_IP=\$(curl -s -4 ifconfig.me 2>/dev/null || echo "81.200.153.155")
fi

echo "   Домен указывает на: \${DOMAIN_IP:-не найден}"
echo "   Сервер имеет IP: \$SERVER_IP"

if [ -n "\$DOMAIN_IP" ] && [ "\$DOMAIN_IP" = "\$SERVER_IP" ]; then
    echo "   ✅ DNS настроен правильно"
else
    echo ""
    echo "⚠️  ВНИМАНИЕ: DNS запись может быть не настроена правильно!"
    echo "   Убедитесь, что DNS записи настроены:"
    echo "   A запись: \$DOMAIN -> \$SERVER_IP"
    echo "   A запись: www.\$DOMAIN -> \$SERVER_IP"
    echo ""
    echo "   Продолжаю получение SSL (certbot проверит DNS сам)..."
fi

echo ""
echo "📜 Получение SSL сертификата..."
echo "   Это может занять несколько минут..."
certbot --nginx -d \$DOMAIN -d www.\$DOMAIN --email \$EMAIL --agree-tos --non-interactive --redirect 2>&1

if [ \$? -eq 0 ]; then
    echo ""
    echo "✅ SSL сертификат успешно получен!"
    echo ""
    echo "🔄 Перезагрузка Nginx..."
    systemctl reload nginx
    
    echo ""
    echo "✅ Готово! Проверьте сайт:"
    echo "   https://\$DOMAIN"
    echo "   https://www.\$DOMAIN"
else
    echo ""
    echo "❌ Ошибка при получении SSL сертификата"
    echo "Проверьте:"
    echo "  1. DNS записи настроены правильно"
    echo "  2. Порты 80 и 443 открыты в firewall"
    echo "  3. Nginx работает корректно"
fi
ENDSSH

