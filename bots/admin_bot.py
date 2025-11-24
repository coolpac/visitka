"""
Admin Bot - Бот для администраторов
Функции:
- Создание рассылки для пользователей user_bot (с поддержкой изображений и кнопок)
- Расширенная статистика пользователей
- Отложенные рассылки
- Сегментация пользователей
- Шаблоны рассылок
- Управление пользователями
- История рассылок
"""
import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputMediaPhoto,
    FSInputFile
)
from aiogram.enums import ParseMode, ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMIN_BOT_TOKEN, USER_BOT_TOKEN, ADMIN_IDS, WEB_APP_URL
from database import Database

# Проверка обязательных параметров
if not ADMIN_BOT_TOKEN:
    raise ValueError("ADMIN_BOT_TOKEN не установлен в переменных окружения. Проверьте файл .env")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=ADMIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация базы данных
db = Database()

# Бот для отправки сообщений пользователям
user_bot = Bot(token=USER_BOT_TOKEN) if USER_BOT_TOKEN else None


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


class BroadcastStates(StatesGroup):
    """Состояния для создания рассылки"""
    waiting_for_content = State()  # Ожидание контента (текст, фото, или фото+текст)
    waiting_for_buttons = State()  # Ожидание кнопок (опционально)
    waiting_for_confirmation = State()  # Ожидание подтверждения
    waiting_for_segment = State()  # Ожидание выбора сегмента


class TemplateStates(StatesGroup):
    """Состояния для работы с шаблонами"""
    waiting_for_template_name = State()
    waiting_for_template_content = State()
    waiting_for_template_buttons = State()


class ScheduledBroadcastStates(StatesGroup):
    """Состояния для отложенной рассылки"""
    waiting_for_content = State()
    waiting_for_buttons = State()
    waiting_for_segment = State()
    waiting_for_datetime = State()
    waiting_for_confirmation = State()


class UserManagementStates(StatesGroup):
    """Состояния для управления пользователями"""
    waiting_for_search = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    
    welcome_text = (
        "👋 <b>Добро пожаловать в Admin Bot!</b>\n\n"
        "🚀 <b>Основные команды:</b>\n"
        "/stats - 📊 Расширенная статистика\n"
        "/broadcast - 📢 Создать рассылку\n"
        "/schedule - ⏰ Отложенная рассылка\n"
        "/templates - 📝 Шаблоны рассылок\n"
        "/users - 👥 Управление пользователями\n"
        "/history - 📜 История рассылок\n"
        "/help - 📖 Полная справка"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="menu_broadcast")],
        [InlineKeyboardButton(text="⏰ Отложенная", callback_data="menu_schedule")],
        [InlineKeyboardButton(text="📝 Шаблоны", callback_data="menu_templates")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="menu_users")],
        [InlineKeyboardButton(text="📜 История", callback_data="menu_history")]
    ])
    
    await message.answer(text=welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    if not is_admin(message.from_user.id):
        return
    
    help_text = (
        "📖 <b>Полная справка по командам:</b>\n\n"
        "📊 <b>Статистика и аналитика:</b>\n"
        "/stats - Расширенная статистика с графиками\n"
        "/analytics - Детальная аналитика\n\n"
        "📢 <b>Рассылки:</b>\n"
        "/broadcast - Мгновенная рассылка (все/сегмент)\n"
        "/schedule - Отложенная рассылка по расписанию\n"
        "/history - История всех рассылок\n\n"
        "📝 <b>Шаблоны:</b>\n"
        "/templates - Управление шаблонами рассылок\n"
        "/template_save - Сохранить текущую рассылку как шаблон\n"
        "/template_list - Список всех шаблонов\n\n"
        "👥 <b>Управление пользователями:</b>\n"
        "/users - Поиск и управление пользователями\n"
        "/user_info - Информация о пользователе\n"
        "/user_block - Заблокировать пользователя\n\n"
        "⚙️ <b>Прочее:</b>\n"
        "/cancel - Отменить текущую операцию\n"
        "/help - Показать эту справку\n\n"
        "💡 <b>Особенности:</b>\n"
        "• Сегментация: новые, активные, неактивные\n"
        "• Отложенные рассылки с планированием\n"
        "• Шаблоны для быстрого создания рассылок\n"
        "• Детальная аналитика и статистика"
    )
    
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Показать расширенную статистику пользователей"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        stats = db.get_detailed_stats()
        total_users = db.get_user_count()
        
        # Получаем статистику по сегментам
        new_users = len(db.get_active_users_by_segment('new'))
        active_users = len(db.get_active_users_by_segment('active'))
        inactive_users = len(db.get_active_users_by_segment('inactive'))
        
        stats_text = (
            "📊 <b>Расширенная статистика</b>\n\n"
            "👥 <b>Пользователи:</b>\n"
            f"• Всего: <b>{stats['total_users']}</b>\n"
            f"• Новые сегодня: <b>{stats['new_today']}</b>\n"
            f"• Новые за неделю: <b>{stats['new_week']}</b>\n"
            f"• Новые за месяц: <b>{stats['new_month']}</b>\n"
            f"• Активные (30 дней): <b>{stats['active_month']}</b>\n\n"
            "📈 <b>Сегменты:</b>\n"
            f"• Новые (7 дней): <b>{new_users}</b>\n"
            f"• Активные (30 дней): <b>{active_users}</b>\n"
            f"• Неактивные: <b>{inactive_users}</b>\n\n"
            "📢 <b>Рассылки:</b>\n"
            f"• Всего рассылок: <b>{stats['total_broadcasts']}</b>\n"
            f"• Отправлено сообщений: <b>{stats['total_sent']}</b>\n"
            f"• Отложенных: <b>{stats['scheduled_broadcasts']}</b>\n\n"
            "Используйте /analytics для детальной аналитики."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 Детальная аналитика", callback_data="analytics_detailed")],
            [InlineKeyboardButton(text="📊 График роста", callback_data="analytics_growth")]
        ])
        
        await message.answer(text=stats_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Ошибка при получении статистики.")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext):
    """Начать создание рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    if not user_bot:
        await message.answer("❌ User Bot не настроен. Проверьте конфигурацию.")
        return
    
    help_text = (
        "📢 <b>Создание рассылки</b>\n\n"
        "Отправьте контент для рассылки:\n"
        "• Текст сообщения\n"
        "• Фото с подписью\n"
        "• Только фото\n\n"
        "После отправки контента вы сможете выбрать сегмент и добавить кнопки.\n\n"
        "Для отмены отправьте /cancel"
    )
    
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)
    await state.set_state(BroadcastStates.waiting_for_content)


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отменить текущую операцию"""
    if not is_admin(message.from_user.id):
        return
    
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных операций для отмены.")
        return
    
    await state.clear()
    await message.answer("❌ Операция отменена.")


@dp.message(BroadcastStates.waiting_for_content)
async def process_broadcast_content(message: types.Message, state: FSMContext):
    """Обработка контента для рассылки (текст или фото)"""
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text or message.caption or ""
    photo_file_id = None
    photo_path = None
    
    # Проверяем, есть ли фото
    if message.photo:
        photo_file_id = message.photo[-1].file_id  # Берем фото наибольшего размера
        # Скачиваем фото для дальнейшей отправки
        try:
            photo_file = await bot.get_file(photo_file_id)
            import os
            os.makedirs("/tmp/broadcast_photos", exist_ok=True)
            photo_path = f"/tmp/broadcast_photos/broadcast_{message.from_user.id}_{message.message_id}.jpg"
            await photo_file.download(photo_path)
        except Exception as e:
            logger.error(f"Ошибка при загрузке фото: {e}")
            await message.answer("❌ Ошибка при загрузке фото. Попробуйте снова.")
            return
    
    if not broadcast_text and not photo_file_id:
        await message.answer("❌ Отправьте текст или фото для рассылки.")
        return
    
    # Сохраняем данные
    await state.update_data(
        broadcast_text=broadcast_text,
        photo_file_id=photo_file_id,
        photo_path=photo_path,
        has_photo=bool(photo_file_id)
    )
    
    # Показываем предпросмотр
    preview_text = "📋 <b>Предпросмотр контента:</b>\n\n"
    if photo_file_id:
        preview_text += "📷 <i>Фото прикреплено</i>\n\n"
    if broadcast_text:
        preview_text += f"{broadcast_text}\n\n"
    
    preview_text += "\nВыберите сегмент для рассылки:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="segment_all"),
            InlineKeyboardButton(text="🆕 Новые (7 дней)", callback_data="segment_new")
        ],
        [
            InlineKeyboardButton(text="✅ Активные (30 дней)", callback_data="segment_active"),
            InlineKeyboardButton(text="😴 Неактивные", callback_data="segment_inactive")
        ]
    ])
    
    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(text=preview_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    await state.set_state(BroadcastStates.waiting_for_segment)


@dp.callback_query(F.data.startswith("segment_"))
async def process_segment_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора сегмента для обычной рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    segment_type = callback.data.replace("segment_", "")
    segment_names = {
        'all': '👥 Все пользователи',
        'new': '🆕 Новые (7 дней)',
        'active': '✅ Активные (30 дней)',
        'inactive': '😴 Неактивные'
    }
    
    await state.update_data(segment_type=segment_type)
    
    await callback.answer(f"Выбран сегмент: {segment_names.get(segment_type, segment_type)}")
    
    # Получаем данные из состояния
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    has_photo = data.get('has_photo', False)
    photo_file_id = data.get('photo_file_id')
    
    preview_text = (
        f"✅ Сегмент выбран: <b>{segment_names.get(segment_type, segment_type)}</b>\n\n"
    )
    
    if has_photo:
        preview_text += "📷 <i>Фото прикреплено</i>\n\n"
    if broadcast_text:
        preview_text += f"{broadcast_text[:200]}...\n\n"
    
    preview_text += "Хотите добавить кнопки? Отправьте:\n"
    preview_text += "• <b>да</b> или <b>кнопки</b> - добавить кнопки\n"
    preview_text += "• <b>нет</b> или <b>пропустить</b> - продолжить без кнопок"
    
    try:
        if has_photo and photo_file_id:
            await callback.message.edit_caption(caption=preview_text, parse_mode=ParseMode.HTML)
            await callback.message.edit_reply_markup(reply_markup=None)
        else:
            await callback.message.edit_text(text=preview_text, parse_mode=ParseMode.HTML)
            await callback.message.edit_reply_markup(reply_markup=None)
    except:
        # Если не удалось отредактировать, отправляем новое сообщение
        if has_photo and photo_file_id:
            await callback.message.answer_photo(
                photo=photo_file_id,
                caption=preview_text,
                parse_mode=ParseMode.HTML
            )
        else:
            await callback.message.answer(text=preview_text, parse_mode=ParseMode.HTML)
    
    await state.set_state(BroadcastStates.waiting_for_buttons)


@dp.message(BroadcastStates.waiting_for_buttons)
async def process_broadcast_buttons(message: types.Message, state: FSMContext):
    """Обработка кнопок для рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    # Если отправили фото вместо текста - игнорируем
    if message.photo:
        await message.answer(
            "⚠️ Вы уже отправили фото.\n"
            "Отправьте ответ на вопрос про кнопки:\n"
            "• <b>да</b> - добавить кнопки\n"
            "• <b>пропустить</b> - продолжить без кнопок",
            parse_mode=ParseMode.HTML
        )
        return
    
    user_input = message.text.lower().strip() if message.text else ""
    
    # Если пользователь хочет пропустить кнопки
    if user_input in ['нет', 'no', 'n', 'пропустить', 'skip', 'продолжить', 'без кнопок']:
        await state.update_data(buttons=None)
        await show_preview_and_confirm(message, state)
        return
    
    # Если пользователь хочет добавить кнопки (но еще не отправил формат)
    if user_input in ['да', 'yes', 'y', 'кнопки', 'buttons', 'добавить кнопки']:
        help_text = (
            "🔘 <b>Добавление кнопок</b>\n\n"
            "Отправьте кнопки в формате:\n"
            "<code>Текст кнопки 1 | https://ссылка1.com\n"
            "Текст кнопки 2 | https://ссылка2.com</code>\n\n"
            "Каждая строка - одна кнопка.\n"
            "Разделитель: <code>|</code>\n\n"
            "Пример:\n"
            "<code>Открыть сайт | https://annaivaschenko.ru\n"
            "Telegram | https://t.me/annet_ivaschenko</code>\n\n"
            "Для пропуска кнопок отправьте: <b>пропустить</b>"
        )
        await message.answer(text=help_text, parse_mode=ParseMode.HTML)
        return
    
    # Парсим кнопки из текста
    if not message.text:
        await message.answer(
            "❌ Отправьте текст с кнопками или <b>пропустить</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    buttons_data = []
    lines = message.text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            if len(parts) == 2:
                button_text = parts[0].strip()
                button_url = parts[1].strip()
                # Проверяем, что это валидный URL
                if button_text and button_url and (
                    button_url.startswith('http://') or 
                    button_url.startswith('https://') or
                    button_url.startswith('tg://') or
                    button_url.startswith('t.me/')
                ):
                    buttons_data.append({
                        'text': button_text,
                        'url': button_url
                    })
    
    if buttons_data:
        await state.update_data(buttons=buttons_data)
        await message.answer(
            f"✅ Добавлено кнопок: {len(buttons_data)}\n"
            "Показываю предпросмотр..."
        )
        await show_preview_and_confirm(message, state)
    else:
        await message.answer(
            "❌ Не удалось распознать кнопки.\n"
            "Проверьте формат:\n"
            "<code>Текст | https://ссылка.com</code>\n\n"
            "Или отправьте <b>пропустить</b> для продолжения без кнопок.",
            parse_mode=ParseMode.HTML
        )


async def show_preview_and_confirm(message: types.Message, state: FSMContext):
    """Показать финальный предпросмотр и запросить подтверждение"""
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    has_photo = data.get('has_photo', False)
    photo_file_id = data.get('photo_file_id')
    buttons_data = data.get('buttons')
    
    preview_text = "📋 <b>Финальный предпросмотр рассылки:</b>\n\n"
    
    if broadcast_text:
        preview_text += f"{broadcast_text}\n\n"
    
    if has_photo:
        preview_text += "📷 <i>С фото</i>\n"
    
    if buttons_data:
        preview_text += f"🔘 <i>Кнопок: {len(buttons_data)}</i>\n"
    
    preview_text += "\nОтправьте <b>да</b> для подтверждения или <b>нет</b> для отмены."
    
    # Создаем клавиатуру для предпросмотра (максимум 3 кнопки)
    preview_keyboard = None
    if buttons_data:
        preview_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
            for btn in buttons_data[:3]
        ])
    
    if has_photo and photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=preview_keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(
            text=preview_text,
            reply_markup=preview_keyboard,
            parse_mode=ParseMode.HTML
        )
    
    await state.set_state(BroadcastStates.waiting_for_confirmation)


@dp.message(BroadcastStates.waiting_for_confirmation)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    """Подтверждение рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    confirmation = message.text.lower().strip()
    
    if confirmation not in ['да', 'yes', 'y', 'ок', 'ok']:
        await message.answer("❌ Рассылка отменена.")
        await state.clear()
        return
    
    # Получаем данные рассылки
    data = await state.get_data()
    broadcast_text = data.get('broadcast_text', '')
    has_photo = data.get('has_photo', False)
    photo_file_id = data.get('photo_file_id')
    photo_path = data.get('photo_path')
    buttons_data = data.get('buttons')
    
    if not broadcast_text and not has_photo:
        await message.answer("❌ Ошибка: контент для рассылки не найден.")
        await state.clear()
        return
    
    # Получаем сегмент из состояния
    segment_type = data.get('segment_type', 'all')
    
    # Получаем список пользователей по сегменту
    user_ids = db.get_active_users_by_segment(segment_type)
    total_users = len(user_ids)
    
    if total_users == 0:
        await message.answer("❌ Нет пользователей для рассылки.")
        await state.clear()
        return
    
    # Создаем клавиатуру с кнопками (если есть)
    keyboard = None
    if buttons_data:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
            for btn in buttons_data
        ])
    
    # Отправляем сообщение о начале рассылки с прогресс-баром
    progress_message = await message.answer(
        "⏳ <b>Начинаю рассылку...</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "▱▱▱▱▱▱▱▱▱▱ 0%\n"
        f"👥 Пользователей: 0/{total_users}\n"
        f"✅ Отправлено: 0\n"
        f"❌ Ошибок: 0",
        parse_mode=ParseMode.HTML
    )
    
    # Отправляем сообщения с анимацией прогресса
    sent_count = 0
    failed_count = 0
    
    for index, user_id in enumerate(user_ids, 1):
        try:
            # Отправляем контент
            if has_photo and photo_path:
                # Используем сохраненный путь к фото
                try:
                    photo_input = FSInputFile(photo_path)
                    await user_bot.send_photo(
                        chat_id=user_id,
                        photo=photo_input,
                        caption=broadcast_text if broadcast_text else None,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML if broadcast_text else None
                    )
                except Exception as e:
                    # Если не удалось отправить через файл, используем file_id
                    logger.warning(f"Не удалось отправить фото через файл, использую file_id: {e}")
                    await user_bot.send_photo(
                        chat_id=user_id,
                        photo=photo_file_id,
                        caption=broadcast_text if broadcast_text else None,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML if broadcast_text else None
                    )
            else:
                # Отправляем только текст с кнопками
                await user_bot.send_message(
                    chat_id=user_id,
                    text=broadcast_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            
            sent_count += 1
            
            # Обновляем прогресс каждые 5 сообщений или в конце
            if index % 5 == 0 or index == total_users:
                progress = int((index / total_users) * 100)
                filled = int(progress / 5)
                empty = 20 - filled
                
                progress_bar = "█" * filled + "▱" * empty
                
                # Эмодзи для анимации
                spinner = ["⏳", "⏳", "⏳", "⏳"][index % 4]
                
                progress_text = (
                    f"{spinner} <b>Рассылка в процессе...</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{progress_bar} {progress}%\n"
                    f"👥 Пользователей: {index}/{total_users}\n"
                    f"✅ Отправлено: {sent_count}\n"
                    f"❌ Ошибок: {failed_count}"
                )
                
                try:
                    await progress_message.edit_text(
                        text=progress_text,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.debug(f"Не удалось обновить прогресс: {e}")
            
            # Небольшая задержка, чтобы не превысить лимиты API
            await asyncio.sleep(0.05)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    
    # Очищаем временный файл фото
    if photo_path:
        try:
            import os
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except:
            pass
    
    # Сохраняем статистику рассылки
    broadcast_content = {
        'text': broadcast_text,
        'has_photo': has_photo,
        'has_buttons': bool(buttons_data),
        'buttons_count': len(buttons_data) if buttons_data else 0,
        'segment_type': segment_type
    }
    
    db.save_broadcast(
        admin_id=message.from_user.id,
        message_text=json.dumps(broadcast_content, ensure_ascii=False),
        sent_count=sent_count,
        failed_count=failed_count
    )
    
    # Финальное сообщение с результатами
    final_text = (
        "✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Отправлено: {sent_count}\n"
        f"❌ Ошибок: {failed_count}\n"
    )
    
    if has_photo:
        final_text += "\n📷 Рассылка содержала фото"
    if buttons_data:
        final_text += f"\n🔘 Кнопок: {len(buttons_data)}"
    
    try:
        await progress_message.edit_text(
            text=final_text,
            parse_mode=ParseMode.HTML
        )
    except:
        await message.answer(text=final_text, parse_mode=ParseMode.HTML)
    
    await state.clear()
    
    logger.info(
        f"Рассылка завершена админом {message.from_user.id}. "
        f"Отправлено: {sent_count}, Ошибок: {failed_count}, "
        f"Фото: {has_photo}, Кнопок: {len(buttons_data) if buttons_data else 0}"
    )


# ==================== ОТЛОЖЕННЫЕ РАССЫЛКИ ====================

@dp.message(Command("schedule"))
async def cmd_schedule(message: types.Message, state: FSMContext):
    """Создать отложенную рассылку"""
    if not is_admin(message.from_user.id):
        return
    
    if not user_bot:
        await message.answer("❌ User Bot не настроен.")
        return
    
    help_text = (
        "⏰ <b>Отложенная рассылка</b>\n\n"
        "Отправьте контент для рассылки:\n"
        "• Текст сообщения\n"
        "• Фото с подписью\n"
        "• Только фото\n\n"
        "После этого вы сможете выбрать сегмент и время отправки.\n\n"
        "Формат времени: <code>DD.MM.YYYY HH:MM</code>\n"
        "Например: <code>25.12.2024 15:30</code>\n\n"
        "Для отмены отправьте /cancel"
    )
    
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)
    await state.set_state(ScheduledBroadcastStates.waiting_for_content)


@dp.message(ScheduledBroadcastStates.waiting_for_content)
async def process_scheduled_content(message: types.Message, state: FSMContext):
    """Обработка контента для отложенной рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    broadcast_text = message.text or message.caption or ""
    photo_file_id = None
    
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    
    if not broadcast_text and not photo_file_id:
        await message.answer("❌ Отправьте текст или фото для рассылки.")
        return
    
    await state.update_data(
        broadcast_text=broadcast_text,
        photo_file_id=photo_file_id,
        has_photo=bool(photo_file_id)
    )
    
    preview_text = "📋 <b>Контент получен</b>\n\n"
    if photo_file_id:
        preview_text += "📷 <i>Фото прикреплено</i>\n\n"
    if broadcast_text:
        preview_text += f"{broadcast_text[:100]}...\n\n"
    
    preview_text += "Выберите сегмент для рассылки:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="sched_segment_all"),
            InlineKeyboardButton(text="🆕 Новые (7 дней)", callback_data="sched_segment_new")
        ],
        [
            InlineKeyboardButton(text="✅ Активные (30 дней)", callback_data="sched_segment_active"),
            InlineKeyboardButton(text="😴 Неактивные", callback_data="sched_segment_inactive")
        ]
    ])
    
    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(text=preview_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    await state.set_state(ScheduledBroadcastStates.waiting_for_segment)


@dp.callback_query(F.data.startswith("sched_segment_"))
async def process_scheduled_segment(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора сегмента для отложенной рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    segment_type = callback.data.replace("sched_segment_", "")
    segment_names = {
        'all': '👥 Все пользователи',
        'new': '🆕 Новые (7 дней)',
        'active': '✅ Активные (30 дней)',
        'inactive': '😴 Неактивные'
    }
    
    await state.update_data(segment_type=segment_type)
    await callback.answer(f"Выбран сегмент: {segment_names.get(segment_type, segment_type)}")
    
    help_text = (
        f"✅ Сегмент: <b>{segment_names.get(segment_type, segment_type)}</b>\n\n"
        "⏰ <b>Укажите время отправки:</b>\n\n"
        "Формат: <code>DD.MM.YYYY HH:MM</code>\n"
        "Примеры:\n"
        "• <code>25.12.2024 15:30</code>\n"
        "• <code>01.01.2025 10:00</code>\n\n"
        "Время указывается в часовом поясе сервера.\n\n"
        "Хотите добавить кнопки? Отправьте:\n"
        "• <b>да</b> - добавить кнопки\n"
        "• <b>пропустить</b> - без кнопок"
    )
    
    await callback.message.edit_caption(caption=help_text, parse_mode=ParseMode.HTML)
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(ScheduledBroadcastStates.waiting_for_buttons)


@dp.message(ScheduledBroadcastStates.waiting_for_buttons)
async def process_scheduled_buttons(message: types.Message, state: FSMContext):
    """Обработка кнопок для отложенной рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    user_input = message.text.lower().strip() if message.text else ""
    
    # Если пользователь хочет пропустить кнопки
    if user_input in ['нет', 'no', 'n', 'пропустить', 'skip', 'без кнопок']:
        await state.update_data(buttons=None)
        await ask_scheduled_datetime(message, state)
        return
    
    # Если пользователь хочет добавить кнопки
    if user_input in ['да', 'yes', 'y', 'кнопки', 'buttons', 'добавить кнопки']:
        help_text = (
            "🔘 <b>Добавление кнопок</b>\n\n"
            "Отправьте кнопки в формате:\n"
            "<code>Текст кнопки 1 | https://ссылка1.com\n"
            "Текст кнопки 2 | https://ссылка2.com</code>\n\n"
            "Для пропуска кнопок отправьте: <b>пропустить</b>"
        )
        await message.answer(text=help_text, parse_mode=ParseMode.HTML)
        return
    
    # Парсим кнопки
    if message.text and '|' in message.text:
        buttons_data = []
        lines = message.text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    button_text = parts[0].strip()
                    button_url = parts[1].strip()
                    if button_text and button_url and (
                        button_url.startswith('http://') or 
                        button_url.startswith('https://') or
                        button_url.startswith('tg://') or
                        button_url.startswith('t.me/')
                    ):
                        buttons_data.append({
                            'text': button_text,
                            'url': button_url
                        })
        
        if buttons_data:
            await state.update_data(buttons=buttons_data)
            await message.answer(f"✅ Добавлено кнопок: {len(buttons_data)}")
            await ask_scheduled_datetime(message, state)
            return
    
    # Если не кнопки, значит это время отправки
    await ask_scheduled_datetime(message, state)


async def ask_scheduled_datetime(message: types.Message, state: FSMContext):
    """Запросить дату и время отправки"""
    help_text = (
        "⏰ <b>Укажите время отправки:</b>\n\n"
        "Формат: <code>DD.MM.YYYY HH:MM</code>\n"
        "Примеры:\n"
        "• <code>25.12.2024 15:30</code>\n"
        "• <code>01.01.2025 10:00</code>\n\n"
        "Время указывается в часовом поясе сервера."
    )
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)
    await state.set_state(ScheduledBroadcastStates.waiting_for_datetime)


@dp.message(ScheduledBroadcastStates.waiting_for_datetime)
async def process_scheduled_datetime(message: types.Message, state: FSMContext):
    """Обработка даты и времени для отложенной рассылки"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # Парсим дату и время
        datetime_str = message.text.strip()
        scheduled_dt = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        
        # Проверяем, что время в будущем
        if scheduled_dt <= datetime.now():
            await message.answer("❌ Время должно быть в будущем!")
            return
        
        data = await state.get_data()
        broadcast_text = data.get('broadcast_text', '')
        has_photo = data.get('has_photo', False)
        photo_file_id = data.get('photo_file_id')
        buttons_data = data.get('buttons')
        segment_type = data.get('segment_type', 'all')
        
        # Сохраняем отложенную рассылку
        buttons_json = json.dumps(buttons_data, ensure_ascii=False) if buttons_data else None
        broadcast_content = {
            'text': broadcast_text,
            'has_photo': has_photo,
            'photo_file_id': photo_file_id,
            'buttons': buttons_data,
            'buttons_count': len(buttons_data) if buttons_data else 0
        }
        
        db.save_scheduled_broadcast(
            admin_id=message.from_user.id,
            message_text=json.dumps(broadcast_content, ensure_ascii=False),
            scheduled_at=scheduled_dt.isoformat(),
            segment_type=segment_type
        )
        
        segment_names = {
            'all': '👥 Все пользователи',
            'new': '🆕 Новые (7 дней)',
            'active': '✅ Активные (30 дней)',
            'inactive': '😴 Неактивные'
        }
        
        success_text = (
            "✅ <b>Отложенная рассылка создана!</b>\n\n"
            f"📅 <b>Время отправки:</b> {scheduled_dt.strftime('%d.%m.%Y %H:%M')}\n"
            f"🎯 <b>Сегмент:</b> {segment_names.get(segment_type, segment_type)}\n"
            f"📝 <b>Контент:</b> {'С фото' if has_photo else 'Текст'}\n"
            f"🔘 <b>Кнопок:</b> {len(buttons_data) if buttons_data else 0}\n\n"
            "Рассылка будет отправлена автоматически в указанное время."
        )
        
        await message.answer(text=success_text, parse_mode=ParseMode.HTML)
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты и времени!\n\n"
            "Используйте формат: <code>DD.MM.YYYY HH:MM</code>\n"
            "Пример: <code>25.12.2024 15:30</code>",
            parse_mode=ParseMode.HTML
        )


# ==================== ШАБЛОНЫ ====================

@dp.message(Command("templates"))
async def cmd_templates(message: types.Message):
    """Показать список шаблонов"""
    if not is_admin(message.from_user.id):
        return
    
    templates = db.get_templates(message.from_user.id)
    
    if not templates:
        await message.answer(
            "📝 <b>Шаблоны рассылок</b>\n\n"
            "У вас пока нет сохраненных шаблонов.\n\n"
            "💡 <b>Как создать шаблон:</b>\n"
            "1. Создайте рассылку через /broadcast\n"
            "2. После успешной рассылки используйте /template_save [название]\n\n"
            "Или создайте новый шаблон прямо сейчас.",
            parse_mode=ParseMode.HTML
        )
        return
    
    text = "📝 <b>Ваши шаблоны:</b>\n\n"
    keyboard_buttons = []
    
    for template in templates[:10]:  # Показываем первые 10
        name = template['name']
        created = datetime.fromisoformat(template['created_at']).strftime("%d.%m.%Y")
        text += f"• <b>{name}</b> (создан {created})\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📄 {name[:30]}",
                callback_data=f"template_use_{template['id']}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🗑 Удалить", callback_data="template_delete_menu"),
        InlineKeyboardButton(text="➕ Создать", callback_data="template_create")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("template_use_"))
async def use_template(callback: types.CallbackQuery, state: FSMContext):
    """Использовать шаблон для рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    template_id = int(callback.data.replace("template_use_", ""))
    template = db.get_template(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    # Загружаем данные шаблона в состояние
    buttons_data = None
    if template['buttons_data']:
        buttons_data = json.loads(template['buttons_data'])
    
    await state.update_data(
        broadcast_text=template['message_text'] or '',
        photo_file_id=template['photo_file_id'],
        has_photo=bool(template['photo_file_id']),
        buttons=buttons_data
    )
    
    await callback.answer(f"✅ Шаблон '{template['name']}' загружен")
    
    # Показываем предпросмотр и запрашиваем сегмент
    preview_text = (
        f"📋 <b>Шаблон: {template['name']}</b>\n\n"
        f"{template['message_text'] or 'Только фото'}\n\n"
        "Выберите сегмент для рассылки:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="segment_all"),
            InlineKeyboardButton(text="🆕 Новые (7 дней)", callback_data="segment_new")
        ],
        [
            InlineKeyboardButton(text="✅ Активные (30 дней)", callback_data="segment_active"),
            InlineKeyboardButton(text="😴 Неактивные", callback_data="segment_inactive")
        ]
    ])
    
    if template['photo_file_id']:
        await callback.message.answer_photo(
            photo=template['photo_file_id'],
            caption=preview_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await callback.message.answer(text=preview_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    await state.set_state(BroadcastStates.waiting_for_segment)


@dp.callback_query(F.data == "template_delete_menu")
async def template_delete_menu(callback: types.CallbackQuery):
    """Меню удаления шаблонов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    templates = db.get_templates(callback.from_user.id)
    
    if not templates:
        await callback.answer("❌ Нет шаблонов для удаления", show_alert=True)
        return
    
    text = "🗑 <b>Выберите шаблон для удаления:</b>\n\n"
    keyboard_buttons = []
    
    for template in templates[:10]:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {template['name'][:30]}",
                callback_data=f"template_delete_{template['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data.startswith("template_delete_"))
async def template_delete(callback: types.CallbackQuery):
    """Удалить шаблон"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    template_id = int(callback.data.replace("template_delete_", ""))
    template = db.get_template(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    if template['admin_id'] != callback.from_user.id:
        await callback.answer("❌ Вы можете удалять только свои шаблоны", show_alert=True)
        return
    
    deleted = db.delete_template(template_id, callback.from_user.id)
    
    if deleted:
        await callback.answer(f"✅ Шаблон '{template['name']}' удален")
        await cmd_templates(callback.message)
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@dp.message(Command("template_save"))
async def cmd_template_save(message: types.Message, state: FSMContext):
    """Сохранить последнюю рассылку как шаблон"""
    if not is_admin(message.from_user.id):
        return
    
    # Получаем последнюю рассылку админа
    broadcasts = db.get_broadcast_stats(limit=1)
    
    if not broadcasts:
        await message.answer(
            "❌ У вас нет завершенных рассылок для сохранения.\n\n"
            "Сначала создайте рассылку через /broadcast"
        )
        return
    
    # Запрашиваем название шаблона
    await message.answer(
        "📝 <b>Создание шаблона</b>\n\n"
        "Отправьте название для шаблона:\n\n"
        "Например: <code>Приветствие новым пользователям</code>",
        parse_mode=ParseMode.HTML
    )
    await state.set_state(TemplateStates.waiting_for_template_name)
    await state.update_data(broadcast_id=broadcasts[0]['id'])


@dp.message(TemplateStates.waiting_for_template_name)
async def process_template_name(message: types.Message, state: FSMContext):
    """Обработка названия шаблона"""
    if not is_admin(message.from_user.id):
        return
    
    template_name = message.text.strip()
    
    if len(template_name) < 3:
        await message.answer("❌ Название должно быть не менее 3 символов.")
        return
    
    # Получаем данные последней рассылки
    data = await state.get_data()
    broadcast_id = data.get('broadcast_id')
    broadcasts = db.get_broadcast_stats(limit=100)
    
    broadcast = None
    for b in broadcasts:
        if b['id'] == broadcast_id:
            broadcast = b
            break
    
    if not broadcast:
        await message.answer("❌ Рассылка не найдена.")
        await state.clear()
        return
    
    # Сохраняем шаблон
    template_id = db.save_template(
        name=template_name,
        admin_id=message.from_user.id,
        message_text=broadcast['message_text'] or '',
        photo_file_id=None,  # Можно расширить для сохранения фото
        buttons_data=None  # Можно расширить для сохранения кнопок
    )
    
    await message.answer(
        f"✅ <b>Шаблон сохранен!</b>\n\n"
        f"📝 Название: <b>{template_name}</b>\n"
        f"🆔 ID: {template_id}\n\n"
        "Используйте /templates для просмотра всех шаблонов.",
        parse_mode=ParseMode.HTML
    )
    
    await state.clear()


# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

@dp.message(Command("users"))
async def cmd_users(message: types.Message, state: FSMContext):
    """Управление пользователями"""
    if not is_admin(message.from_user.id):
        return
    
    help_text = (
        "👥 <b>Управление пользователями</b>\n\n"
        "Отправьте для поиска:\n"
        "• ID пользователя (число)\n"
        "• Имя пользователя\n"
        "• Username (без @)\n\n"
        "Или используйте команды:\n"
        "/user_info [ID] - Информация о пользователе\n"
        "/user_block [ID] - Заблокировать/разблокировать\n\n"
        "Для отмены отправьте /cancel"
    )
    
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)
    await state.set_state(UserManagementStates.waiting_for_search)


@dp.message(UserManagementStates.waiting_for_search)
async def process_user_search(message: types.Message, state: FSMContext):
    """Обработка поиска пользователей"""
    if not is_admin(message.from_user.id):
        return
    
    query = message.text.strip()
    users = db.search_users(query)
    
    if not users:
        await message.answer("❌ Пользователи не найдены.")
        await state.clear()
        return
    
    if len(users) == 1:
        # Показываем детальную информацию
        user = users[0]
        user_text = (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 <b>ID:</b> {user['user_id']}\n"
            f"📛 <b>Имя:</b> {user['first_name'] or 'не указано'}\n"
            f"📛 <b>Фамилия:</b> {user['last_name'] or 'не указано'}\n"
            f"🔗 <b>Username:</b> @{user['username'] or 'не указан'}\n"
            f"🔑 <b>Start параметр:</b> {user['start_param'] or 'не указан'}\n"
            f"📅 <b>Регистрация:</b> {datetime.fromisoformat(user['registered_at']).strftime('%d.%m.%Y %H:%M')}\n"
            f"🕐 <b>Последняя активность:</b> {datetime.fromisoformat(user['last_activity']).strftime('%d.%m.%Y %H:%M')}\n"
            f"✅ <b>Статус:</b> {'Активен' if user['is_active'] else 'Заблокирован'}\n"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚫 Заблокировать" if user['is_active'] else "✅ Разблокировать",
                    callback_data=f"user_toggle_{user['user_id']}"
                )
            ]
        ])
        
        await message.answer(text=user_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        # Показываем список
        text = f"🔍 <b>Найдено пользователей: {len(users)}</b>\n\n"
        keyboard_buttons = []
        
        for user in users[:10]:
            name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or "Без имени"
            username = f"@{user['username']}" if user['username'] else "нет username"
            text += f"• {name} ({username}) - ID: {user['user_id']}\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👤 {name[:20]}",
                    callback_data=f"user_info_{user['user_id']}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.answer(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    await state.clear()


@dp.callback_query(F.data.startswith("user_toggle_"))
async def toggle_user_status(callback: types.CallbackQuery):
    """Переключить статус пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    user_id = int(callback.data.replace("user_toggle_", ""))
    success = db.toggle_user_active(user_id)
    
    if success:
        user_info = db.get_user_info(user_id)
        if user_info:
            status = "заблокирован" if not user_info['is_active'] else "разблокирован"
            await callback.answer(f"✅ Пользователь {status}")
            await callback.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🚫 Заблокировать" if user_info['is_active'] else "✅ Разблокировать",
                            callback_data=f"user_toggle_{user_id}"
                        )
                    ]
                ])
            )
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@dp.callback_query(F.data.startswith("user_info_"))
async def show_user_info_callback(callback: types.CallbackQuery):
    """Показать информацию о пользователе через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    user_id = int(callback.data.replace("user_info_", ""))
    user = db.get_user_info(user_id)
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    user_text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 <b>ID:</b> {user['user_id']}\n"
        f"📛 <b>Имя:</b> {user['first_name'] or 'не указано'}\n"
        f"📛 <b>Фамилия:</b> {user['last_name'] or 'не указано'}\n"
        f"🔗 <b>Username:</b> @{user['username'] or 'не указан'}\n"
        f"🔑 <b>Start параметр:</b> {user['start_param'] or 'не указан'}\n"
        f"📅 <b>Регистрация:</b> {datetime.fromisoformat(user['registered_at']).strftime('%d.%m.%Y %H:%M')}\n"
        f"🕐 <b>Последняя активность:</b> {datetime.fromisoformat(user['last_activity']).strftime('%d.%m.%Y %H:%M')}\n"
        f"✅ <b>Статус:</b> {'Активен' if user['is_active'] else 'Заблокирован'}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚫 Заблокировать" if user['is_active'] else "✅ Разблокировать",
                callback_data=f"user_toggle_{user_id}"
            )
        ]
    ])
    
    await callback.message.edit_text(text=user_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


# ==================== АНАЛИТИКА ====================

@dp.message(Command("analytics"))
async def cmd_analytics(message: types.Message):
    """Детальная аналитика"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        stats = db.get_detailed_stats()
        date_stats = db.get_user_stats_by_date(days=30)
        
        # Формируем график роста (текстовый)
        growth_chart = "📈 <b>Рост пользователей (последние 30 дней):</b>\n\n"
        
        if date_stats:
            # Берем последние 7 дней для компактности
            recent_stats = date_stats[:7]
            max_count = max([s['count'] for s in recent_stats], default=1)
            
            for stat in reversed(recent_stats):
                date_str = stat['date']
                try:
                    # Парсим дату из SQLite формата YYYY-MM-DD
                    if isinstance(date_str, str):
                        if 'T' in date_str:
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        date_obj = datetime.fromisoformat(str(date_str))
                    date = date_obj.strftime("%d.%m")
                except Exception as e:
                    logger.warning(f"Ошибка парсинга даты {date_str}: {e}")
                    date = str(date_str)[:5]
                
                count = stat['count']
                bar_length = int((count / max_count) * 20) if max_count > 0 else 0
                bar = "█" * bar_length + "▱" * (20 - bar_length)
                growth_chart += f"{date}: {bar} {count}\n"
        else:
            growth_chart += "Нет данных за этот период\n"
        
        analytics_text = (
            "📊 <b>Детальная аналитика</b>\n\n"
            f"{growth_chart}\n"
            "📈 <b>Общая статистика:</b>\n"
            f"• Всего пользователей: <b>{stats['total_users']}</b>\n"
            f"• Новые сегодня: <b>{stats['new_today']}</b>\n"
            f"• Новые за неделю: <b>{stats['new_week']}</b>\n"
            f"• Новые за месяц: <b>{stats['new_month']}</b>\n"
            f"• Активные (30 дней): <b>{stats['active_month']}</b>\n\n"
            "📢 <b>Рассылки:</b>\n"
            f"• Всего рассылок: <b>{stats['total_broadcasts']}</b>\n"
            f"• Отправлено сообщений: <b>{stats['total_sent']}</b>\n"
            f"• Отложенных: <b>{stats['scheduled_broadcasts']}</b>\n\n"
            "💡 <b>Метрики:</b>\n"
        )
        
        # Вычисляем метрики
        if stats['total_users'] > 0:
            active_rate = (stats['active_month'] / stats['total_users']) * 100
            analytics_text += f"• Процент активных: <b>{active_rate:.1f}%</b>\n"
        else:
            analytics_text += "• Процент активных: <b>0%</b>\n"
        
        if stats['total_broadcasts'] > 0 and stats['total_sent'] > 0:
            avg_per_broadcast = stats['total_sent'] / stats['total_broadcasts']
            analytics_text += f"• Среднее сообщений на рассылку: <b>{avg_per_broadcast:.0f}</b>\n"
        else:
            analytics_text += "• Среднее сообщений на рассылку: <b>0</b>\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📈 График роста", callback_data="analytics_growth")],
            [InlineKeyboardButton(text="📊 Экспорт данных", callback_data="analytics_export")]
        ])
        
        await message.answer(text=analytics_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Ошибка при получении аналитики: {e}")
        await message.answer("❌ Ошибка при получении аналитики.")


@dp.callback_query(F.data == "analytics_detailed")
async def analytics_detailed(callback: types.CallbackQuery):
    """Детальная аналитика через callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    if callback.message:
        await cmd_analytics(callback.message)
    else:
        await bot.send_message(callback.from_user.id, "Используйте команду /analytics")


@dp.callback_query(F.data == "analytics_growth")
async def analytics_growth(callback: types.CallbackQuery):
    """График роста пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        date_stats = db.get_user_stats_by_date(days=30)
        
        if not date_stats:
            await callback.answer("Нет данных для графика", show_alert=True)
            if callback.message:
                await callback.message.answer("📈 <b>График роста пользователей</b>\n\nНет данных за последние 30 дней.", parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(callback.from_user.id, "Нет данных для графика")
            return
        
        await callback.answer()
        
        growth_chart = "📈 <b>График роста пользователей (30 дней):</b>\n\n"
        
        # Показываем все дни
        max_count = max([s['count'] for s in date_stats], default=1)
        
        for stat in reversed(date_stats[:30]):  # Последние 30 дней
            # SQLite возвращает дату в формате YYYY-MM-DD
            date_str = stat['date']
            try:
                # Пробуем разные форматы
                if isinstance(date_str, str):
                    if 'T' in date_str:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        # Формат YYYY-MM-DD
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    date_obj = datetime.fromisoformat(str(date_str))
                
                date_formatted = date_obj.strftime("%d.%m")
            except Exception as e:
                logger.warning(f"Ошибка парсинга даты {date_str}: {e}")
                date_formatted = str(date_str)[:5]  # Берем первые 5 символов
            
            count = stat['count']
            bar_length = int((count / max_count) * 30) if max_count > 0 else 0
            bar = "█" * bar_length + "▱" * (30 - bar_length)
            growth_chart += f"{date_formatted}: {bar} {count}\n"
        
        if callback.message:
            try:
                await callback.message.edit_text(text=growth_chart, parse_mode=ParseMode.HTML)
            except:
                await callback.message.answer(text=growth_chart, parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(callback.from_user.id, text=growth_chart, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Ошибка при построении графика: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при построении графика", show_alert=True)


@dp.callback_query(F.data == "analytics_export")
async def analytics_export(callback: types.CallbackQuery):
    """Экспорт данных аналитики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        stats = db.get_detailed_stats()
        date_stats = db.get_user_stats_by_date(days=30)
        
        export_text = "📊 <b>Экспорт данных аналитики</b>\n\n"
        export_text += "📈 <b>Статистика пользователей:</b>\n"
        export_text += f"Всего: {stats['total_users']}\n"
        export_text += f"Новые сегодня: {stats['new_today']}\n"
        export_text += f"Новые за неделю: {stats['new_week']}\n"
        export_text += f"Новые за месяц: {stats['new_month']}\n"
        export_text += f"Активные (30 дней): {stats['active_month']}\n\n"
        
        export_text += "📢 <b>Статистика рассылок:</b>\n"
        export_text += f"Всего рассылок: {stats['total_broadcasts']}\n"
        export_text += f"Отправлено сообщений: {stats['total_sent']}\n"
        export_text += f"Отложенных: {stats['scheduled_broadcasts']}\n\n"
        
        if date_stats:
            export_text += "📅 <b>Регистрации по датам (последние 30 дней):</b>\n"
            for stat in reversed(date_stats[:30]):
                date_str = stat['date']
                try:
                    # Парсим дату из SQLite формата YYYY-MM-DD
                    if isinstance(date_str, str):
                        if 'T' in date_str:
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        date_obj = datetime.fromisoformat(str(date_str))
                    date = date_obj.strftime("%d.%m.%Y")
                except Exception as e:
                    logger.warning(f"Ошибка парсинга даты {date_str}: {e}")
                    date = str(date_str)
                export_text += f"{date}: {stat['count']}\n"
        
        # Отправляем как файл (в виде текста, так как Telegram Bot API не поддерживает CSV напрямую)
        await callback.message.answer(
            text=export_text,
            parse_mode=ParseMode.HTML
        )
        
        await callback.answer("✅ Данные экспортированы")
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте: {e}")
        await callback.answer("❌ Ошибка при экспорте", show_alert=True)


# ==================== ИСТОРИЯ РАССЫЛОК ====================

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    """Показать историю рассылок"""
    if not is_admin(message.from_user.id):
        return
    
    broadcasts = db.get_broadcast_stats(limit=20)
    
    if not broadcasts:
        await message.answer("📜 История рассылок пуста.")
        return
    
    text = "📜 <b>История рассылок:</b>\n\n"
    
    for broadcast in broadcasts[:10]:
        created = datetime.fromisoformat(broadcast['created_at']).strftime("%d.%m.%Y %H:%M")
        content = json.loads(broadcast['message_text']) if broadcast['message_text'] else {}
        
        text += (
            f"📅 <b>{created}</b>\n"
            f"✅ Отправлено: {broadcast['sent_count']}\n"
            f"❌ Ошибок: {broadcast['failed_count']}\n"
        )
        
        if content.get('segment_type'):
            segment_names = {
                'all': '👥 Все',
                'new': '🆕 Новые',
                'active': '✅ Активные',
                'inactive': '😴 Неактивные'
            }
            text += f"🎯 Сегмент: {segment_names.get(content['segment_type'], content['segment_type'])}\n"
        
        if content.get('has_photo'):
            text += "📷 С фото\n"
        if content.get('buttons_count', 0) > 0:
            text += f"🔘 Кнопок: {content['buttons_count']}\n"
        
        text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Детальная статистика", callback_data="history_detailed")]
    ])
    
    await message.answer(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


# ==================== CALLBACK ОБРАБОТЧИКИ МЕНЮ ====================

@dp.callback_query(F.data == "menu_stats")
async def menu_stats(callback: types.CallbackQuery):
    """Обработка меню статистики"""
    logger.info(f"Получен callback menu_stats от пользователя {callback.from_user.id}")
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        logger.info(f"Callback menu_stats обработан для пользователя {callback.from_user.id}")
        
        # Используем callback.message.answer вместо передачи callback.message в функцию
        if callback.message:
            await cmd_stats(callback.message)
        else:
            # Если message недоступен, отправляем через бота
            await bot.send_message(callback.from_user.id, "Используйте команду /stats")
    except Exception as e:
        logger.error(f"Ошибка в menu_stats: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "menu_broadcast")
async def menu_broadcast(callback: types.CallbackQuery, state: FSMContext):
    """Обработка меню рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        
        if callback.message:
            await cmd_broadcast(callback.message, state)
        else:
            await bot.send_message(callback.from_user.id, "Используйте команду /broadcast")
    except Exception as e:
        logger.error(f"Ошибка в menu_broadcast: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "menu_schedule")
async def menu_schedule(callback: types.CallbackQuery, state: FSMContext):
    """Обработка меню отложенной рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        
        if callback.message:
            await cmd_schedule(callback.message, state)
        else:
            await bot.send_message(callback.from_user.id, "Используйте команду /schedule")
    except Exception as e:
        logger.error(f"Ошибка в menu_schedule: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "menu_templates")
async def menu_templates(callback: types.CallbackQuery):
    """Обработка меню шаблонов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        
        if callback.message:
            await cmd_templates(callback.message)
        else:
            await bot.send_message(callback.from_user.id, "Используйте команду /templates")
    except Exception as e:
        logger.error(f"Ошибка в menu_templates: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "menu_users")
async def menu_users(callback: types.CallbackQuery, state: FSMContext):
    """Обработка меню пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        
        if callback.message:
            await cmd_users(callback.message, state)
        else:
            await bot.send_message(callback.from_user.id, "Используйте команду /users")
    except Exception as e:
        logger.error(f"Ошибка в menu_users: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "menu_history")
async def menu_history(callback: types.CallbackQuery):
    """Обработка меню истории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        # Отвечаем на callback сразу
        await callback.answer()
        
        if callback.message:
            await cmd_history(callback.message)
        else:
            await bot.send_message(callback.from_user.id, "Используйте команду /history")
    except Exception as e:
        logger.error(f"Ошибка в menu_history: {e}", exc_info=True)
        try:
            await callback.answer("❌ Ошибка", show_alert=True)
        except:
            pass


@dp.callback_query(F.data == "history_detailed")
async def history_detailed(callback: types.CallbackQuery):
    """Детальная история рассылок"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    broadcasts = db.get_broadcast_stats(limit=50)
    
    if not broadcasts:
        await callback.answer("История пуста", show_alert=True)
        return
    
    text = "📜 <b>Детальная история рассылок:</b>\n\n"
    
    total_sent = sum(b['sent_count'] for b in broadcasts)
    total_failed = sum(b['failed_count'] for b in broadcasts)
    
    text += f"📊 <b>Общая статистика:</b>\n"
    text += f"Всего рассылок: {len(broadcasts)}\n"
    text += f"Отправлено сообщений: {total_sent}\n"
    text += f"Ошибок: {total_failed}\n"
    if (total_sent + total_failed) > 0:
        success_rate = (total_sent / (total_sent + total_failed)) * 100
        text += f"Успешность: {success_rate:.1f}%\n\n"
    else:
        text += "Успешность: 0%\n\n"
    
    text += "📅 <b>Последние рассылки:</b>\n\n"
    
    for broadcast in broadcasts[:15]:
        created = datetime.fromisoformat(broadcast['created_at']).strftime("%d.%m %H:%M")
        content = json.loads(broadcast['message_text']) if broadcast['message_text'] else {}
        
        text += f"📅 {created}\n"
        text += f"✅ {broadcast['sent_count']} | ❌ {broadcast['failed_count']}\n"
        
        if content.get('segment_type'):
            segment_names = {
                'all': '👥 Все',
                'new': '🆕 Новые',
                'active': '✅ Активные',
                'inactive': '😴 Неактивные'
            }
            text += f"🎯 {segment_names.get(content['segment_type'], content['segment_type'])}\n"
        
        text += "\n"
    
    await callback.message.edit_text(text=text, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик всех остальных сообщений"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "Используйте команды:\n"
        "/start - Начать работу\n"
        "/stats - Статистика\n"
        "/broadcast - Создать рассылку\n"
        "/schedule - Отложенная рассылка\n"
        "/templates - Шаблоны\n"
        "/users - Управление пользователями\n"
        "/history - История рассылок\n"
        "/help - Справка"
    )


async def check_scheduled_broadcasts():
    """Проверка и отправка отложенных рассылок"""
    while True:
        try:
            scheduled = db.get_scheduled_broadcasts()
            now = datetime.now()
            
            for broadcast in scheduled:
                scheduled_time = datetime.fromisoformat(broadcast['scheduled_at'])
                
                # Если время наступило (с запасом в 1 минуту)
                if scheduled_time <= now:
                    try:
                        await send_scheduled_broadcast(broadcast)
                        # Помечаем рассылку как выполненную
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            'UPDATE broadcasts SET is_scheduled = 0 WHERE id = ?',
                            (broadcast['id'],)
                        )
                        conn.commit()
                        conn.close()
                        logger.info(f"Отложенная рассылка {broadcast['id']} отправлена")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке отложенной рассылки {broadcast['id']}: {e}")
            
            # Проверяем каждую минуту
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике рассылок: {e}")
            await asyncio.sleep(60)


async def send_scheduled_broadcast(broadcast: dict):
    """Отправить отложенную рассылку"""
    if not user_bot:
        return
    
    content = json.loads(broadcast['message_text'])
    segment_type = broadcast.get('segment_type', 'all')
    
    # Получаем пользователей по сегменту
    user_ids = db.get_active_users_by_segment(segment_type)
    
    # Создаем клавиатуру
    keyboard = None
    if content.get('buttons'):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn['text'], url=btn['url'])]
            for btn in content['buttons']
        ])
    
    sent_count = 0
    failed_count = 0
    
    # Отправляем сообщения
    for user_id in user_ids:
        try:
            if content.get('has_photo') and content.get('photo_file_id'):
                await user_bot.send_photo(
                    chat_id=user_id,
                    photo=content['photo_file_id'],
                    caption=content.get('text'),
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML if content.get('text') else None
                )
            else:
                await user_bot.send_message(
                    chat_id=user_id,
                    text=content.get('text', ''),
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed_count += 1
            logger.error(f"Ошибка при отправке отложенной рассылки пользователю {user_id}: {e}")
    
    # Обновляем статистику
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE broadcasts SET sent_count = ?, failed_count = ? WHERE id = ?',
        (sent_count, failed_count, broadcast['id'])
    )
    conn.commit()
    conn.close()
    
    # Уведомляем админа
    try:
        await bot.send_message(
            chat_id=broadcast['admin_id'],
            text=(
                f"⏰ <b>Отложенная рассылка отправлена!</b>\n\n"
                f"✅ Отправлено: {sent_count}\n"
                f"❌ Ошибок: {failed_count}",
            ),
            parse_mode=ParseMode.HTML
        )
    except:
        pass


async def main():
    """Главная функция для запуска бота"""
    logger.info("Запуск Admin Bot...")
    
    # Проверяем подключение к базе данных
    try:
        user_count = db.get_user_count()
        logger.info(f"База данных подключена. Всего пользователей: {user_count}")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return
    
    # Проверяем наличие администраторов
    if not ADMIN_IDS:
        logger.warning("Список администраторов пуст!")
    
    # Запускаем планировщик отложенных рассылок
    scheduler_task = asyncio.create_task(check_scheduled_broadcasts())
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        scheduler_task.cancel()
        await bot.session.close()
        if user_bot:
            await user_bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

