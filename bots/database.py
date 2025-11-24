"""
Модуль для работы с базой данных пользователей
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

class Database:
    def __init__(self, db_file: str = 'bots/database.db'):
        """
        Инициализация базы данных
        
        Args:
            db_file: Путь к файлу базы данных
        """
        # Создаем директорию, если её нет
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Инициализация таблиц базы данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                start_param TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Таблица рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message_text TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP,
                is_scheduled INTEGER DEFAULT 0,
                segment_type TEXT
            )
        ''')
        
        # Таблица шаблонов рассылок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS broadcast_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                admin_id INTEGER,
                message_text TEXT,
                photo_file_id TEXT,
                buttons_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица активности пользователей (для аналитики)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                activity_date DATE,
                activity_count INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Создаем индексы для оптимизации запросов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_registered ON users(registered_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_broadcasts_created ON broadcasts(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity(activity_date)')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: Optional[str] = None, 
                 first_name: Optional[str] = None, last_name: Optional[str] = None,
                 start_param: Optional[str] = None) -> bool:
        """
        Добавить нового пользователя
        
        Returns:
            True если пользователь новый, False если уже существует
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Обновляем информацию о пользователе
            cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, 
                    start_param = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (username, first_name, last_name, start_param, user_id))
            conn.commit()
            conn.close()
            return False
        else:
            # Добавляем нового пользователя
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, start_param)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, start_param))
            conn.commit()
            conn.close()
            return True
    
    def get_user_count(self) -> int:
        """Получить общее количество пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_active_users(self) -> List[int]:
        """Получить список ID активных пользователей"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def save_broadcast(self, admin_id: int, message_text: str, 
                      sent_count: int, failed_count: int):
        """Сохранить информацию о рассылке"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcasts (admin_id, message_text, sent_count, failed_count)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, message_text, sent_count, failed_count))
        conn.commit()
        conn.close()
    
    def get_broadcast_stats(self, limit: int = 10) -> List[Dict]:
        """Получить статистику рассылок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM broadcasts 
            WHERE is_scheduled = 0
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_user_stats_by_date(self, days: int = 30) -> List[Dict]:
        """Получить статистику регистраций по датам"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DATE(registered_at) as date, COUNT(*) as count
            FROM users
            WHERE registered_at >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(registered_at)
            ORDER BY date DESC
        ''', (days,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_active_users_by_segment(self, segment_type: str) -> List[int]:
        """
        Получить пользователей по сегменту
        
        Args:
            segment_type: Тип сегмента ('new' - новые за 7 дней, 'active' - активные за 30 дней, 'all' - все)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if segment_type == 'new':
            cursor.execute('''
                SELECT user_id FROM users 
                WHERE is_active = 1 
                AND registered_at >= datetime('now', '-7 days')
            ''')
        elif segment_type == 'active':
            cursor.execute('''
                SELECT user_id FROM users 
                WHERE is_active = 1 
                AND last_activity >= datetime('now', '-30 days')
            ''')
        elif segment_type == 'inactive':
            cursor.execute('''
                SELECT user_id FROM users 
                WHERE is_active = 1 
                AND last_activity < datetime('now', '-30 days')
            ''')
        else:  # 'all'
            cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
    
    def search_users(self, query: str) -> List[Dict]:
        """Поиск пользователей по имени, username или ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Пытаемся найти по ID
        try:
            user_id = int(query)
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return [dict(result)]
        except ValueError:
            pass
        
        # Поиск по имени или username
        search_pattern = f'%{query}%'
        cursor.execute('''
            SELECT * FROM users 
            WHERE first_name LIKE ? OR last_name LIKE ? OR username LIKE ?
            ORDER BY registered_at DESC
            LIMIT 20
        ''', (search_pattern, search_pattern, search_pattern))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def toggle_user_active(self, user_id: int) -> bool:
        """Переключить статус активности пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT is_active FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        new_status = 0 if result[0] else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE user_id = ?', (new_status, user_id))
        conn.commit()
        conn.close()
        return True
    
    def save_template(self, name: str, admin_id: int, message_text: str, 
                     photo_file_id: Optional[str] = None, buttons_data: Optional[str] = None) -> int:
        """Сохранить шаблон рассылки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcast_templates (name, admin_id, message_text, photo_file_id, buttons_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, admin_id, message_text, photo_file_id, buttons_data))
        conn.commit()
        template_id = cursor.lastrowid
        conn.close()
        return template_id
    
    def get_templates(self, admin_id: Optional[int] = None) -> List[Dict]:
        """Получить список шаблонов"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if admin_id:
            cursor.execute('''
                SELECT * FROM broadcast_templates 
                WHERE admin_id = ?
                ORDER BY created_at DESC
            ''', (admin_id,))
        else:
            cursor.execute('''
                SELECT * FROM broadcast_templates 
                ORDER BY created_at DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Получить шаблон по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM broadcast_templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def delete_template(self, template_id: int, admin_id: int) -> bool:
        """Удалить шаблон"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM broadcast_templates 
            WHERE id = ? AND admin_id = ?
        ''', (template_id, admin_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def save_scheduled_broadcast(self, admin_id: int, message_text: str, 
                                 scheduled_at: str, segment_type: str = 'all',
                                 photo_file_id: Optional[str] = None, 
                                 buttons_data: Optional[str] = None) -> int:
        """Сохранить отложенную рассылку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO broadcasts (admin_id, message_text, scheduled_at, is_scheduled, segment_type)
            VALUES (?, ?, ?, 1, ?)
        ''', (admin_id, message_text, scheduled_at, segment_type))
        conn.commit()
        broadcast_id = cursor.lastrowid
        conn.close()
        return broadcast_id
    
    def get_scheduled_broadcasts(self) -> List[Dict]:
        """Получить список отложенных рассылок"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM broadcasts 
            WHERE is_scheduled = 1 AND scheduled_at > datetime('now')
            ORDER BY scheduled_at ASC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_detailed_stats(self) -> Dict:
        """Получить детальную статистику"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        stats['total_users'] = cursor.fetchone()[0]
        
        # Новые пользователи за сегодня
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE DATE(registered_at) = DATE('now') AND is_active = 1
        ''')
        stats['new_today'] = cursor.fetchone()[0]
        
        # Новые пользователи за неделю
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE registered_at >= datetime('now', '-7 days') AND is_active = 1
        ''')
        stats['new_week'] = cursor.fetchone()[0]
        
        # Новые пользователи за месяц
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE registered_at >= datetime('now', '-30 days') AND is_active = 1
        ''')
        stats['new_month'] = cursor.fetchone()[0]
        
        # Активные пользователи за последние 30 дней
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM users 
            WHERE last_activity >= datetime('now', '-30 days') AND is_active = 1
        ''')
        stats['active_month'] = cursor.fetchone()[0]
        
        # Всего рассылок
        cursor.execute('SELECT COUNT(*) FROM broadcasts WHERE is_scheduled = 0')
        stats['total_broadcasts'] = cursor.fetchone()[0]
        
        # Всего отправлено сообщений
        cursor.execute('SELECT SUM(sent_count) FROM broadcasts WHERE is_scheduled = 0')
        result = cursor.fetchone()[0]
        stats['total_sent'] = result if result else 0
        
        # Отложенных рассылок
        cursor.execute('SELECT COUNT(*) FROM broadcasts WHERE is_scheduled = 1')
        stats['scheduled_broadcasts'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


