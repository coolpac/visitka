#!/bin/bash

# Скрипт проверки деплоя
# Использование: ./check-deployment.sh [user@server]

SERVER=${1:-"root@81.200.153.155"}
DOMAIN="annaivaschenko.ru"

echo "🔍 Проверка деплоя проекта"
echo "Сервер: $SERVER"
echo "Домен: $DOMAIN"
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверка подключения
echo -n "Проверка подключения к серверу... "
if ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

# Проверка файлов
echo -n "Проверка файлов проекта... "
if ssh "$SERVER" "[ -f /var/www/annaivaschenko.ru/index.html ]"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Проверка ботов
echo -n "Проверка User Bot... "
if ssh "$SERVER" "systemctl is-active --quiet user-bot.service"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

echo -n "Проверка Admin Bot... "
if ssh "$SERVER" "systemctl is-active --quiet admin-bot.service"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Проверка Nginx
echo -n "Проверка Nginx... "
if ssh "$SERVER" "systemctl is-active --quiet nginx"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Проверка SSL
echo -n "Проверка SSL сертификата... "
if ssh "$SERVER" "[ -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${YELLOW}⚠️  SSL не настроен${NC}"
fi

# Проверка DNS
echo -n "Проверка DNS... "
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
if [ -n "$DOMAIN_IP" ]; then
    echo -e "${GREEN}✅ ($DOMAIN_IP)${NC}"
else
    echo -e "${RED}❌${NC}"
fi

# Проверка доступности сайта
echo -n "Проверка доступности сайта... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✅ (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}❌ (HTTP $HTTP_CODE)${NC}"
fi

echo ""
echo "📊 Статистика:"
ssh "$SERVER" << 'ENDSSH'
echo "  Пользователей в базе: $(sqlite3 /var/www/annaivaschenko.ru/bots/database.db 'SELECT COUNT(*) FROM users' 2>/dev/null || echo '0')"
echo "  Размер проекта: $(du -sh /var/www/annaivaschenko.ru 2>/dev/null | cut -f1)"
echo "  Использование диска: $(df -h /var/www | tail -1 | awk '{print $5}')"
ENDSSH

echo ""
echo "📝 Последние логи User Bot:"
ssh "$SERVER" "tail -n 5 /var/log/annaivaschenko/user-bot.log 2>/dev/null || echo 'Логи не найдены'"

echo ""
echo "📝 Последние логи Admin Bot:"
ssh "$SERVER" "tail -n 5 /var/log/annaivaschenko/admin-bot.log 2>/dev/null || echo 'Логи не найдены'"

