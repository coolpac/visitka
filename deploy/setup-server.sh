#!/bin/bash

# Скрипт первоначальной настройки сервера
# Запускать на сервере: bash <(curl -s https://raw.githubusercontent.com/your-repo/setup-server.sh)
# Или скопировать и запустить локально

set -e

DOMAIN="annaivaschenko.ru"
REMOTE_DIR="/var/www/annaivaschenko.ru"

echo "🚀 Настройка сервера для $DOMAIN"
echo ""

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "📦 Установка необходимых пакетов..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    ufw \
    fail2ban

# Настройка firewall
echo "🔥 Настройка firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Создание пользователя и директорий
echo "👤 Настройка пользователя и директорий..."
sudo mkdir -p $REMOTE_DIR
sudo mkdir -p $REMOTE_DIR/bots
sudo mkdir -p $REMOTE_DIR/logs
sudo mkdir -p /var/log/annaivaschenko

# Создание пользователя www-data если его нет
if ! id "www-data" &>/dev/null; then
    sudo useradd -r -s /bin/false www-data
fi

# Настройка прав
sudo chown -R www-data:www-data $REMOTE_DIR
sudo chown -R www-data:www-data /var/log/annaivaschenko
sudo chmod -R 755 $REMOTE_DIR

# Настройка Nginx базовой конфигурации
echo "🌐 Настройка Nginx..."
sudo systemctl enable nginx
sudo systemctl start nginx

# Настройка fail2ban
echo "🛡️  Настройка fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Оптимизация системы
echo "⚙️  Оптимизация системы..."

# Увеличение лимитов файлов
sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
* soft nofile 65536
* hard nofile 65536
EOF

# Настройка sysctl для производительности
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF
# Оптимизация для веб-сервера
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65535
EOF

sudo sysctl -p

echo ""
echo "✅ Настройка сервера завершена!"
echo ""
echo "Следующие шаги:"
echo "  1. Настройте DNS записи для домена:"
echo "     A запись: $DOMAIN -> $(curl -s ifconfig.me)"
echo "     A запись: www.$DOMAIN -> $(curl -s ifconfig.me)"
echo ""
echo "  2. Загрузите проект на сервер"
echo ""
echo "  3. После настройки DNS, получите SSL сертификат:"
echo "     sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"

