# ⚙️ Быстрая настройка .env файла

## 🚀 Быстрый старт

```bash
cd bots
cp .env.example .env
nano .env  # или используйте любой редактор
```

## 📝 Что нужно заполнить

1. **USER_BOT_TOKEN** - токен User Bot от @BotFather
2. **ADMIN_BOT_TOKEN** - токен Admin Bot от @BotFather  
3. **ADMIN_BOT_CHAT_ID** - ID чата для уведомлений
4. **ADMIN_IDS** - ваш Telegram ID (или несколько через запятую)
5. **WEB_APP_URL** - https://annaivaschenko.ru

## 📖 Подробная инструкция

См. **[bots/ENV_SETUP.md](bots/ENV_SETUP.md)** для пошаговой инструкции с примерами.

## ✅ Пример заполненного файла

```env
USER_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_BOT_TOKEN=9876543210:XYZwvuTSRqpoNMLkjihGFEdcba
ADMIN_BOT_CHAT_ID=123456789
ADMIN_IDS=123456789
WEB_APP_URL=https://annaivaschenko.ru
DATABASE_FILE=bots/database.db
```

## 🔒 Важно

- ⚠️ Не публикуйте `.env` файл в git
- ⚠️ Храните токены в безопасности
- ⚠️ Файл уже добавлен в `.gitignore`

