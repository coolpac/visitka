"""
User Bot - Бот для пользователей
Функции:
- Приветственное сообщение по /start
- Кнопка для открытия мини-приложения
- Сбор start параметров
- Отправка уведомлений в админ бот о новых пользователях
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from config import USER_BOT_TOKEN, ADMIN_BOT_TOKEN, ADMIN_BOT_CHAT_ID, WEB_APP_URL
from database import Database

# Проверка обязательных параметров
if not USER_BOT_TOKEN:
    raise ValueError("USER_BOT_TOKEN не установлен в переменных окружения. Проверьте файл .env")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=USER_BOT_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
db = Database()

# Бот для отправки уведомлений админу
admin_bot = Bot(token=ADMIN_BOT_TOKEN) if ADMIN_BOT_TOKEN else None


async def send_notification_to_admin(user_id: int, username: str, 
                                     first_name: str, start_param: str, 
                                     total_users: int):
    """
    Отправить уведомление в админ бот о новом пользователе
    
    Args:
        user_id: ID пользователя
        username: Username пользователя
        first_name: Имя пользователя
        start_param: Start параметр
        total_users: Общее количество пользователей
    """
    if not admin_bot or not ADMIN_BOT_CHAT_ID:
        logger.warning("Админ бот не настроен, уведомление не отправлено")
        return
    
    try:
        # Формируем сообщение
        message_text = (
            "🆕 <b>Новый пользователь!</b>\n\n"
            f"👤 <b>ID:</b> {user_id}\n"
            f"📛 <b>Имя:</b> {first_name}\n"
        )
        
        if username:
            message_text += f"🔗 <b>Username:</b> @{username}\n"
        
        if start_param:
            message_text += f"🔑 <b>Start параметр:</b> {start_param}\n"
        
        message_text += f"\n📊 <b>Всего пользователей:</b> {total_users}"
        
        await admin_bot.send_message(
            chat_id=ADMIN_BOT_CHAT_ID,
            text=message_text,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Уведомление отправлено админу о пользователе {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления админу: {e}")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение с кнопкой для открытия мини-приложения
    """
    user = message.from_user
    user_id = user.id
    
    # Получаем start параметр из команды
    start_param = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]
    
    # Добавляем пользователя в базу данных
    is_new_user = db.add_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        start_param=start_param
    )
    
    # Формируем приветственное сообщение
    welcome_text = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я бот-помощник Анны Алексеевны Иващенко.\n\n"
        "Нажмите на кнопку ниже, чтобы открыть мини-приложение "
        "и узнать больше о профессиональной деятельности, проектах и опыте работы."
    )
    
    # Создаем клавиатуру с кнопкой Web App
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Открыть мини-приложение",
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            ]
        ]
    )
    
    # Отправляем сообщение
    await message.answer(
        text=welcome_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    
    # Если пользователь новый, отправляем уведомление админу
    if is_new_user:
        total_users = db.get_user_count()
        await send_notification_to_admin(
            user_id=user_id,
            username=user.username or "не указан",
            first_name=user.first_name or "не указано",
            start_param=start_param or "не указан",
            total_users=total_users
        )
        logger.info(f"Новый пользователь зарегистрирован: {user_id} (@{user.username})")
    else:
        logger.info(f"Пользователь вернулся: {user_id} (@{user.username})")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "Используйте кнопку в меню для открытия мини-приложения."
    )
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик всех остальных сообщений"""
    # Обновляем время последней активности
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Отправляем подсказку
    await message.answer(
        "👋 Используйте команду /start для начала работы с ботом.\n\n"
        "Или нажмите на кнопку в меню для открытия мини-приложения."
    )


async def main():
    """Главная функция для запуска бота"""
    logger.info("Запуск User Bot...")
    
    # Проверяем подключение к базе данных
    try:
        user_count = db.get_user_count()
        logger.info(f"База данных подключена. Всего пользователей: {user_count}")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()
        if admin_bot:
            await admin_bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

