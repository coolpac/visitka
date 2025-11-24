# 🚀 Деплой проекта на продакшен

Полное руководство по развертыванию проекта на сервере `81.200.153.155` с доменом `annaivaschenko.ru`.

## 📋 Содержание

1. [Подготовка проекта](#подготовка-проекта)
2. [Настройка сервера](#настройка-сервера)
3. [Деплой](#деплой)
4. [Настройка SSL](#настройка-ssl)
5. [Мониторинг и обслуживание](#мониторинг-и-обслуживание)

## 🔧 Подготовка проекта

### 1. Проверьте файлы проекта

Убедитесь, что все файлы на месте:
- `index.html` - главная страница
- `styles.css` - стили
- `script.js` - JavaScript
- `telegram-webapp.js` - интеграция Telegram
- `bots/` - папка с ботами
- `images/` - изображения

### 2. Настройте .env файл для ботов

Создайте файл `bots/.env` с вашими токенами:

```bash
cd bots
cp .env.example .env
nano .env
```

Заполните:
```env
USER_BOT_TOKEN=ваш_токен_юзер_бота
ADMIN_BOT_TOKEN=ваш_токен_админ_бота
ADMIN_BOT_CHAT_ID=ваш_telegram_id
ADMIN_IDS=ваш_telegram_id
WEB_APP_URL=https://annaivaschenko.ru
```

### 3. Обновите URL в коде

Убедитесь, что в `bots/config.py` и `telegram-webapp.js` указан правильный URL:
- `WEB_APP_URL=https://annaivaschenko.ru`

## 🖥️ Настройка сервера

### Вариант 1: Автоматическая настройка

Запустите скрипт настройки на сервере:

```bash
ssh root@81.200.153.155
bash <(curl -s https://raw.githubusercontent.com/your-repo/setup-server.sh)
```

Или скопируйте `deploy/setup-server.sh` на сервер и запустите:

```bash
scp deploy/setup-server.sh root@81.200.153.155:/tmp/
ssh root@81.200.153.155 "bash /tmp/setup-server.sh"
```

### Вариант 2: Ручная настройка

#### 1. Подключитесь к серверу

```bash
ssh root@81.200.153.155
```

#### 2. Обновите систему

```bash
apt update && apt upgrade -y
```

#### 3. Установите необходимые пакеты

```bash
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git curl ufw fail2ban
```

#### 4. Настройте firewall

```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

#### 5. Создайте директории

```bash
mkdir -p /var/www/annaivaschenko.ru/bots
mkdir -p /var/www/annaivaschenko.ru/logs
mkdir -p /var/log/annaivaschenko
chown -R www-data:www-data /var/www/annaivaschenko.ru
chown -R www-data:www-data /var/log/annaivaschenko
```

## 📦 Деплой

### Автоматический деплой

Используйте скрипт `deploy.sh`:

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh root@81.200.153.155
```

Скрипт автоматически:
- ✅ Скопирует все файлы на сервер
- ✅ Настроит Python окружение
- ✅ Установит зависимости
- ✅ Настроит systemd сервисы для ботов
- ✅ Настроит Nginx
- ✅ Запустит боты

### Ручной деплой

#### 1. Копирование файлов

```bash
# С локальной машины
rsync -avz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
    ./ root@81.200.153.155:/var/www/annaivaschenko.ru/
```

#### 2. Настройка Python окружения

```bash
ssh root@81.200.153.155
cd /var/www/annaivaschenko.ru/bots
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### 3. Настройка .env

```bash
nano /var/www/annaivaschenko.ru/bots/.env
# Заполните все необходимые значения
chmod 600 /var/www/annaivaschenko.ru/bots/.env
chown www-data:www-data /var/www/annaivaschenko.ru/bots/.env
```

#### 4. Установка systemd сервисов

```bash
# Копируем файлы сервисов
cp deploy/user-bot.service /etc/systemd/system/
cp deploy/admin-bot.service /etc/systemd/system/

# Обновляем пути в файлах (если нужно)
nano /etc/systemd/system/user-bot.service
nano /etc/systemd/system/admin-bot.service

# Активируем сервисы
systemctl daemon-reload
systemctl enable user-bot.service
systemctl enable admin-bot.service
systemctl start user-bot.service
systemctl start admin-bot.service
```

#### 5. Настройка Nginx

```bash
# Копируем конфигурацию
cp deploy/nginx.conf /etc/nginx/sites-available/annaivaschenko.ru

# Создаем символическую ссылку
ln -s /etc/nginx/sites-available/annaivaschenko.ru /etc/nginx/sites-enabled/

# Проверяем конфигурацию
nginx -t

# Перезагружаем Nginx
systemctl reload nginx
```

## 🔒 Настройка SSL

### 1. Настройте DNS записи

В панели управления доменом добавьте:
- **A запись**: `annaivaschenko.ru` → `81.200.153.155`
- **A запись**: `www.annaivaschenko.ru` → `81.200.153.155`

Подождите 5-15 минут для распространения DNS.

### 2. Получите SSL сертификат

```bash
ssh root@81.200.153.155
certbot --nginx -d annaivaschenko.ru -d www.annaivaschenko.ru
```

Следуйте инструкциям certbot. Он автоматически:
- ✅ Получит SSL сертификат от Let's Encrypt
- ✅ Настроит Nginx для HTTPS
- ✅ Настроит автоматическое обновление сертификата

### 3. Активируйте HTTPS в Nginx

После получения сертификата, раскомментируйте HTTPS секцию в `/etc/nginx/sites-available/annaivaschenko.ru`:

```bash
nano /etc/nginx/sites-available/annaivaschenko.ru
# Раскомментируйте блок server с listen 443
```

Проверьте и перезагрузите:

```bash
nginx -t
systemctl reload nginx
```

## 📊 Мониторинг и обслуживание

### Проверка статуса ботов

```bash
systemctl status user-bot.service
systemctl status admin-bot.service
```

### Просмотр логов

```bash
# Логи ботов
tail -f /var/log/annaivaschenko/user-bot.log
tail -f /var/log/annaivaschenko/admin-bot.log

# Логи ошибок
tail -f /var/log/annaivaschenko/user-bot.error.log
tail -f /var/log/annaivaschenko/admin-bot.error.log

# Логи Nginx
tail -f /var/log/nginx/annaivaschenko.ru.access.log
tail -f /var/log/nginx/annaivaschenko.ru.error.log
```

### Перезапуск ботов

```bash
systemctl restart user-bot.service
systemctl restart admin-bot.service
```

### Перезапуск Nginx

```bash
systemctl restart nginx
```

### Обновление проекта

После изменений в коде:

```bash
# С локальной машины
./deploy/deploy.sh root@81.200.153.155

# Или вручную
ssh root@81.200.153.155
cd /var/www/annaivaschenko.ru
git pull  # если используете git
# или rsync файлы
systemctl restart user-bot.service
systemctl restart admin-bot.service
```

## 🔍 Проверка работоспособности

### 1. Проверьте сайт

Откройте в браузере:
- http://annaivaschenko.ru
- https://annaivaschenko.ru (после настройки SSL)

### 2. Проверьте ботов

- Отправьте `/start` вашему User Bot
- Отправьте `/start` вашему Admin Bot

### 3. Проверьте мини-приложение

- Откройте User Bot в Telegram
- Нажмите кнопку "Открыть мини-приложение"
- Убедитесь, что сайт открывается корректно

## 🛠️ Решение проблем

### Бот не запускается

```bash
# Проверьте логи
journalctl -u user-bot.service -n 50
journalctl -u admin-bot.service -n 50

# Проверьте .env файл
cat /var/www/annaivaschenko.ru/bots/.env

# Проверьте права доступа
ls -la /var/www/annaivaschenko.ru/bots/
```

### Nginx не работает

```bash
# Проверьте конфигурацию
nginx -t

# Проверьте статус
systemctl status nginx

# Проверьте логи
tail -f /var/log/nginx/error.log
```

### SSL сертификат не работает

```bash
# Проверьте сертификат
certbot certificates

# Обновите вручную
certbot renew --dry-run
```

## 📝 Чеклист деплоя

- [ ] Сервер настроен и обновлен
- [ ] Python и зависимости установлены
- [ ] Nginx установлен и настроен
- [ ] DNS записи настроены
- [ ] Проект скопирован на сервер
- [ ] .env файл настроен
- [ ] Боты запущены и работают
- [ ] SSL сертификат получен
- [ ] HTTPS работает
- [ ] Сайт открывается
- [ ] Мини-приложение работает в Telegram

## 🔐 Безопасность

1. **Не храните .env в git** - добавьте в .gitignore
2. **Используйте сильные пароли** для SSH
3. **Настройте fail2ban** для защиты от брутфорса
4. **Регулярно обновляйте систему**: `apt update && apt upgrade`
5. **Настройте бэкапы** базы данных ботов
6. **Мониторьте логи** на подозрительную активность

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи
2. Проверьте статус сервисов
3. Убедитесь, что все файлы на месте
4. Проверьте права доступа

