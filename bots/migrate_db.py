#!/usr/bin/env python3
"""
Скрипт для миграции базы данных
Выполняет обновление схемы БД, добавляя недостающие колонки
"""
import sys
import os
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from database import Database

def main():
    """Выполнить миграцию базы данных"""
    print("🔄 Запуск миграции базы данных...")
    
    try:
        db = Database()
        print("✅ Миграция выполнена успешно!")
        print("📊 Проверка структуры таблицы broadcasts...")
        
        # Проверяем структуру таблицы
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(broadcasts)")
        columns = cursor.fetchall()
        
        print("\n📋 Колонки в таблице broadcasts:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Проверяем наличие нужных колонок
        column_names = [col[1] for col in columns]
        required_columns = ['scheduled_at', 'is_scheduled', 'segment_type']
        
        print("\n✅ Проверка обязательных колонок:")
        for col_name in required_columns:
            if col_name in column_names:
                print(f"  ✓ {col_name} - присутствует")
            else:
                print(f"  ✗ {col_name} - ОТСУТСТВУЕТ!")
        
        conn.close()
        
        print("\n✅ Миграция завершена!")
        return 0
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграции: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

