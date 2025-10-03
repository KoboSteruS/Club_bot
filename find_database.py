#!/usr/bin/env python3
"""
Скрипт для поиска базы данных на сервере.
"""

import os
import glob
from pathlib import Path

def find_database_files():
    """Поиск файлов базы данных."""
    print("🔍 Поиск файлов базы данных...")
    
    # Возможные пути
    search_paths = [
        ".",
        "data",
        "..",
        "/root",
        "/home",
        "/var"
    ]
    
    # Расширения файлов БД
    extensions = ["*.db", "*.sqlite", "*.sqlite3"]
    
    found_files = []
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            print(f"📁 Проверяем: {search_path}")
            
            for ext in extensions:
                pattern = os.path.join(search_path, "**", ext)
                files = glob.glob(pattern, recursive=True)
                
                for file in files:
                    if os.path.isfile(file):
                        size = os.path.getsize(file)
                        print(f"  📄 {file} ({size} bytes)")
                        found_files.append((file, size))
    
    return found_files

def check_database_structure(db_path):
    """Проверка структуры базы данных."""
    try:
        import sqlite3
        
        print(f"\n🔍 Проверяем структуру: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Проверяем chat_activities
        if any(table[0] == 'chat_activities' for table in tables):
            print("\n✅ Таблица chat_activities найдена!")
            
            # Проверяем структуру
            cursor.execute("PRAGMA table_info(chat_activities)")
            columns = cursor.fetchall()
            
            print("📋 Колонки в chat_activities:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
            # Проверяем нужные колонки
            column_names = [col[1] for col in columns]
            needed_columns = ['media_file_id', 'media_duration', 'media_file_size']
            
            missing_columns = [col for col in needed_columns if col not in column_names]
            if missing_columns:
                print(f"\n❌ Отсутствующие колонки: {missing_columns}")
                return False
            else:
                print(f"\n✅ Все нужные колонки присутствуют!")
                return True
        else:
            print("\n❌ Таблица chat_activities не найдена!")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Главная функция."""
    print("🚀 Поиск базы данных...")
    
    # Ищем файлы БД
    found_files = find_database_files()
    
    if not found_files:
        print("\n❌ Файлы базы данных не найдены!")
        return
    
    print(f"\n📊 Найдено {len(found_files)} файлов базы данных:")
    
    # Проверяем каждый найденный файл
    for db_path, size in found_files:
        if size > 1024:  # Только файлы больше 1KB
            print(f"\n{'='*50}")
            print(f"📄 {db_path}")
            print(f"📊 Размер: {size:,} bytes")
            
            if check_database_structure(db_path):
                print(f"\n✅ {db_path} - подходящая база данных!")
                print(f"💡 Обновите путь в migrate_db.py на: {db_path}")
                break
        else:
            print(f"\n⚠️ {db_path} - слишком маленький файл ({size} bytes), пропускаем")

if __name__ == "__main__":
    main()
