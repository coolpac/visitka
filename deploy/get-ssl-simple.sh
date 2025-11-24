#!/bin/bash

# Упрощенный скрипт для получения SSL
# Использование: ./get-ssl-simple.sh [email]

SERVER="root@81.200.153.155"
DOMAIN="annaivaschenko.ru"
EMAIL="${1:-kirill123658@gmail.com}"

echo "🔒 Получение SSL сертификата для $DOMAIN"
echo "Email: $EMAIL"
echo ""

ssh "$SERVER" "certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL сертификат успешно получен!"
    echo ""
    echo "Проверьте сайт:"
    echo "  https://$DOMAIN"
    echo "  https://www.$DOMAIN"
else
    echo ""
    echo "❌ Ошибка при получении SSL сертификата"
    echo ""
    echo "Возможные причины:"
    echo "  1. DNS записи еще не распространились (подождите 5-15 минут)"
    echo "  2. Порты 80/443 не открыты"
    echo "  3. Nginx не работает"
    echo ""
    echo "Проверьте вручную:"
    echo "  ssh $SERVER"
    echo "  certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

