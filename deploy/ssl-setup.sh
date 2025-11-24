#!/bin/bash

# Скрипт для настройки SSL сертификата
# Использование: ./ssl-setup.sh

set -e

DOMAIN="annaivaschenko.ru"
EMAIL="your-email@example.com"  # Замените на ваш email

echo "🔒 Настройка SSL сертификата для $DOMAIN"
echo ""

# Проверка, что Nginx установлен
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx не установлен. Установите его сначала."
    exit 1
fi

# Проверка, что certbot установлен
if ! command -v certbot &> /dev/null; then
    echo "📦 Установка certbot..."
    sudo apt install -y certbot python3-certbot-nginx
fi

# Проверка DNS
echo "🔍 Проверка DNS записей..."
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP=$(curl -s ifconfig.me)

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "⚠️  Внимание: DNS запись может быть не настроена правильно"
    echo "   Домен указывает на: $DOMAIN_IP"
    echo "   Сервер имеет IP: $SERVER_IP"
    echo ""
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Получение SSL сертификата
echo "📜 Получение SSL сертификата..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive --redirect

# Настройка автоматического обновления
echo "🔄 Настройка автоматического обновления сертификата..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Проверка конфигурации Nginx
echo "✅ Проверка конфигурации Nginx..."
sudo nginx -t

# Перезагрузка Nginx
echo "🔄 Перезагрузка Nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ SSL сертификат настроен успешно!"
echo ""
echo "Проверьте сайт:"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""
echo "Сертификат будет автоматически обновляться каждые 60 дней."

