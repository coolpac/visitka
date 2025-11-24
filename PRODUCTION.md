# 🚀 Продакшен деплой - annaivaschenko.ru

Полное руководство по развертыванию проекта на продакшен сервер.

## 📋 Информация о сервере

- **Домен**: annaivaschenko.ru
- **IP**: 81.200.153.155
- **Сервер**: Linux (Ubuntu/Debian)

## ⚡ Быстрый старт

См. [deploy/QUICKSTART.md](deploy/QUICKSTART.md) для быстрого деплоя за 5 минут.

## 📁 Структура проекта

```
visitka/
├── index.html              # Главная страница
├── styles.css              # Стили
├── script.js               # JavaScript
├── telegram-webapp.js      # Интеграция Telegram
├── images/                 # Изображения
├── bots/                   # Telegram боты
│   ├── user_bot.py        # User Bot
│   ├── admin_bot.py       # Admin Bot
│   └── .env               # Конфигурация (не в git)
└── deploy/                 # Файлы деплоя
    ├── nginx.conf         # Конфигурация Nginx
    ├── user-bot.service   # Systemd сервис User Bot
    ├── admin-bot.service  # Systemd сервис Admin Bot
    ├── deploy.sh          # Скрипт деплоя
    └── setup-server.sh    # Настройка сервера
```

## 🔧 Подготовка к деплою

### 1. Настройте .env файл

```bash
cd bots
cp .env.example .env
nano .env
```

Обязательные параметры:
- `USER_BOT_TOKEN` - токен User Bot от @BotFather
- `ADMIN_BOT_TOKEN` - токен Admin Bot от @BotFather
- `ADMIN_BOT_CHAT_ID` - ваш Telegram ID
- `ADMIN_IDS` - ID администраторов (через запятую)
- `WEB_APP_URL` - https://annaivaschenko.ru

### 2. Убедитесь, что все файлы готовы

Проверьте наличие всех файлов:
- HTML, CSS, JS файлы
- Изображения в папке `images/`
- Боты в папке `bots/`

## 🚀 Деплой

### Автоматический деплой (рекомендуется)

```bash
# 1. Настройка сервера (один раз)
scp deploy/setup-server.sh root@81.200.153.155:/tmp/
ssh root@81.200.153.155 "bash /tmp/setup-server.sh"

# 2. Деплой проекта
./deploy/deploy.sh root@81.200.153.155
```

### Ручной деплой

См. подробные инструкции в [deploy/README.md](deploy/README.md)

## 🔒 Настройка SSL

После настройки DNS:

```bash
ssh root@81.200.153.155
cd /var/www/annaivaschenko.ru/deploy
nano ssl-setup.sh  # Укажите ваш email
./ssl-setup.sh
```

Или вручную:

```bash
certbot --nginx -d annaivaschenko.ru -d www.annaivaschenko.ru
```

## ✅ Проверка деплоя

```bash
./deploy/check-deployment.sh root@81.200.153.155
```

Или проверьте вручную:

```bash
# Статус ботов
ssh root@81.200.153.155 "systemctl status user-bot.service admin-bot.service"

# Логи
ssh root@81.200.153.155 "tail -f /var/log/annaivaschenko/user-bot.log"

# Сайт
curl -I https://annaivaschenko.ru
```

## 🔄 Обновление проекта

После изменений в коде:

```bash
./deploy/deploy.sh root@81.200.153.155
```

Боты автоматически перезапустятся.

## 📊 Мониторинг

### Логи ботов

```bash
# User Bot
tail -f /var/log/annaivaschenko/user-bot.log

# Admin Bot
tail -f /var/log/annaivaschenko/admin-bot.log

# Ошибки
tail -f /var/log/annaivaschenko/*.error.log
```

### Логи Nginx

```bash
tail -f /var/log/nginx/annaivaschenko.ru.access.log
tail -f /var/log/nginx/annaivaschenko.ru.error.log
```

### Статус сервисов

```bash
systemctl status user-bot.service
systemctl status admin-bot.service
systemctl status nginx
```

## 🛠️ Управление

### Перезапуск ботов

```bash
systemctl restart user-bot.service
systemctl restart admin-bot.service
```

### Остановка ботов

```bash
systemctl stop user-bot.service
systemctl stop admin-bot.service
```

### Перезапуск Nginx

```bash
systemctl reload nginx
# или
systemctl restart nginx
```

## 🔐 Безопасность

1. ✅ SSL сертификат настроен
2. ✅ Firewall настроен (UFW)
3. ✅ Fail2ban установлен
4. ✅ .env файл не в git
5. ✅ Права доступа настроены

## 📞 Поддержка

При проблемах:

1. Проверьте логи
2. Проверьте статус сервисов
3. Проверьте конфигурацию
4. См. [deploy/README.md](deploy/README.md) для детальной информации

## 📝 Чеклист

- [ ] Сервер настроен
- [ ] Проект задеплоен
- [ ] DNS настроен
- [ ] SSL сертификат получен
- [ ] Боты работают
- [ ] Сайт открывается
- [ ] Мини-приложение работает в Telegram

