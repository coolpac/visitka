"""
Конфигурационный файл для Telegram ботов
"""
import os
from pathlib import Path

# Путь к файлу .env (в папке bots)
env_path = Path(__file__).parent / '.env'

# Пытаемся загрузить переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # Если python-dotenv не установлен, используем переменные окружения системы
    pass

# Токены ботов (получите у @BotFather)
USER_BOT_TOKEN = os.getenv('USER_BOT_TOKEN', '')
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN', '')

# ID админ бота (для отправки уведомлений)
ADMIN_BOT_CHAT_ID = os.getenv('ADMIN_BOT_CHAT_ID', '')

# ID администраторов (кто может использовать админ бота)
ADMIN_IDS = [
    int(admin_id) for admin_id in os.getenv('ADMIN_IDS', '').split(',') if admin_id
]

# URL мини-приложения (ваш сайт-визитка)
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://annaivaschenko.ru')

# База данных
DATABASE_FILE = os.getenv('DATABASE_FILE', 'bots/database.db')

# Проверка обязательных параметров (только при импорте модулей ботов)
# Раскомментируйте эти проверки после настройки .env файла
# if not USER_BOT_TOKEN:
#     raise ValueError("USER_BOT_TOKEN не установлен в переменных окружения")
# if not ADMIN_BOT_TOKEN:
#     raise ValueError("ADMIN_BOT_TOKEN не установлен в переменных окружения")
# if not ADMIN_BOT_CHAT_ID:
#     raise ValueError("ADMIN_BOT_CHAT_ID не установлен в переменных окружения")

