#!/bin/bash

# Скрипт деплоя проекта на продакшен сервер
# Использование: ./deploy.sh [user@server]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Параметры
SERVER=${1:-"root@81.200.153.155"}
DOMAIN="annaivaschenko.ru"
REMOTE_DIR="/var/www/annaivaschenko.ru"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}🚀 Начало деплоя на продакшен${NC}"
echo -e "Сервер: ${YELLOW}$SERVER${NC}"
echo -e "Домен: ${YELLOW}$DOMAIN${NC}"
echo ""

# Проверка подключения к серверу
echo -e "${YELLOW}📡 Проверка подключения к серверу...${NC}"
if ! ssh -o ConnectTimeout=5 "$SERVER" "echo 'OK'" > /dev/null 2>&1; then
    echo -e "${RED}❌ Не удалось подключиться к серверу${NC}"
    echo "Проверьте:"
    echo "  1. Доступность сервера"
    echo "  2. SSH ключи настроены"
    echo "  3. Правильный пользователь и IP"
    exit 1
fi
echo -e "${GREEN}✅ Подключение установлено${NC}"

# Создание директорий на сервере
echo -e "${YELLOW}📁 Создание директорий на сервере...${NC}"
ssh "$SERVER" "mkdir -p $REMOTE_DIR/bots $REMOTE_DIR/logs /var/log/annaivaschenko"

# Обновление версии файлов для обхода кеша
echo -e "${YELLOW}🔄 Обновление версии файлов...${NC}"
if [ -f "$LOCAL_DIR/update-version.sh" ]; then
    bash "$LOCAL_DIR/update-version.sh"
fi

# Копирование файлов проекта
echo -e "${YELLOW}📦 Копирование файлов проекта...${NC}"
rsync -avz --exclude='.git' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='database.db' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    "$LOCAL_DIR/" "$SERVER:$REMOTE_DIR/"

# Установка зависимостей Python на сервере
echo -e "${YELLOW}🐍 Настройка Python окружения...${NC}"
ssh "$SERVER" << 'ENDSSH'
cd /var/www/annaivaschenko.ru/bots

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Активация и установка зависимостей
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
ENDSSH

# Настройка прав доступа
echo -e "${YELLOW}🔐 Настройка прав доступа...${NC}"
ssh "$SERVER" "chown -R www-data:www-data $REMOTE_DIR"
ssh "$SERVER" "chmod -R 755 $REMOTE_DIR"
ssh "$SERVER" "chmod -R 755 /var/log/annaivaschenko"

# Копирование .env файла (если существует локально)
if [ -f "$LOCAL_DIR/bots/.env" ]; then
    echo -e "${YELLOW}⚙️  Копирование .env файла...${NC}"
    scp "$LOCAL_DIR/bots/.env" "$SERVER:$REMOTE_DIR/bots/.env"
    ssh "$SERVER" "chmod 600 $REMOTE_DIR/bots/.env"
    ssh "$SERVER" "chown www-data:www-data $REMOTE_DIR/bots/.env"
else
    echo -e "${YELLOW}⚠️  .env файл не найден локально${NC}"
    echo "Создайте .env файл на сервере вручную:"
    echo "  ssh $SERVER"
    echo "  nano $REMOTE_DIR/bots/.env"
fi

# Установка systemd сервисов
echo -e "${YELLOW}⚙️  Настройка systemd сервисов...${NC}"
scp "$LOCAL_DIR/deploy/user-bot.service" "$SERVER:/tmp/user-bot.service"
scp "$LOCAL_DIR/deploy/admin-bot.service" "$SERVER:/tmp/admin-bot.service"

ssh "$SERVER" << 'ENDSSH'
sudo mv /tmp/user-bot.service /etc/systemd/system/user-bot.service
sudo mv /tmp/admin-bot.service /etc/systemd/system/admin-bot.service
sudo systemctl daemon-reload
sudo systemctl enable user-bot.service
sudo systemctl enable admin-bot.service
ENDSSH

# Настройка Nginx
echo -e "${YELLOW}🌐 Настройка Nginx...${NC}"
scp "$LOCAL_DIR/deploy/nginx.conf" "$SERVER:/tmp/annaivaschenko.ru.conf"

ssh "$SERVER" << 'ENDSSH'
sudo mv /tmp/annaivaschenko.ru.conf /etc/nginx/sites-available/annaivaschenko.ru
sudo ln -sf /etc/nginx/sites-available/annaivaschenko.ru /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
ENDSSH

# Перезапуск ботов
echo -e "${YELLOW}🔄 Перезапуск ботов...${NC}"
ssh "$SERVER" << 'ENDSSH'
sudo systemctl restart user-bot.service
sudo systemctl restart admin-bot.service
sudo systemctl status user-bot.service --no-pager
sudo systemctl status admin-bot.service --no-pager
ENDSSH

echo ""
echo -e "${GREEN}✅ Деплой завершен успешно!${NC}"
echo ""
echo "Следующие шаги:"
echo "  1. Настройте DNS записи для домена:"
echo "     A запись: annaivaschenko.ru -> 81.200.153.155"
echo "     A запись: www.annaivaschenko.ru -> 81.200.153.155"
echo ""
echo "  2. После настройки DNS, получите SSL сертификат:"
echo "     ssh $SERVER"
echo "     sudo certbot --nginx -d annaivaschenko.ru -d www.annaivaschenko.ru"
echo ""
echo "  3. Проверьте статус ботов:"
echo "     sudo systemctl status user-bot.service"
echo "     sudo systemctl status admin-bot.service"
echo ""
echo "  4. Проверьте логи:"
echo "     sudo tail -f /var/log/annaivaschenko/user-bot.log"
echo "     sudo tail -f /var/log/annaivaschenko/admin-bot.log"

