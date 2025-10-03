#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления недостающих колонок.

Этот скрипт добавляет новые колонки в таблицу chat_activities:
- media_file_id
- media_duration  
- media_file_size
"""

import asyncio
import aiosqlite
import os
from pathlib import Path
from loguru import logger

# Настройка логирования
logger.add("logs/migration.log", rotation="1 MB", level="DEBUG")

DATABASE_PATH = "club_bot.db"
BACKUP_PATH = "club_bot_backup.db"

async def backup_database():
    """Создание резервной копии базы данных."""
    try:
        if os.path.exists(DATABASE_PATH):
            # Копируем файл базы данных
            with open(DATABASE_PATH, 'rb') as src:
                with open(BACKUP_PATH, 'wb') as dst:
                    dst.write(src.read())
            logger.info(f"✅ Резервная копия создана: {BACKUP_PATH}")
        else:
            logger.warning(f"⚠️ База данных не найдена: {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"❌ Ошибка создания резервной копии: {e}")
        raise

async def check_column_exists(cursor, table_name, column_name):
    """Проверка существования колонки в таблице."""
    try:
        await cursor.execute(f"PRAGMA table_info({table_name})")
        columns = await cursor.fetchall()
        return any(col[1] == column_name for col in columns)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки колонки {column_name}: {e}")
        return False

async def migrate_database():
    """Выполнение миграции базы данных."""
    try:
        # Создаем резервную копию
        await backup_database()
        
        # Подключаемся к базе данных
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.cursor()
            
            logger.info("🔍 Проверяем существующие колонки в таблице chat_activities...")
            
            # Проверяем существование таблицы
            await cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_activities'")
            if not await cursor.fetchone():
                logger.error("❌ Таблица chat_activities не найдена!")
                return False
            
            # Колонки для добавления
            new_columns = [
                ("media_file_id", "VARCHAR(100)"),
                ("media_duration", "INTEGER"), 
                ("media_file_size", "INTEGER")
            ]
            
            # Добавляем недостающие колонки
            for column_name, column_type in new_columns:
                if not await check_column_exists(cursor, "chat_activities", column_name):
                    logger.info(f"➕ Добавляем колонку: {column_name}")
                    await cursor.execute(f"ALTER TABLE chat_activities ADD COLUMN {column_name} {column_type}")
                    await db.commit()
                    logger.info(f"✅ Колонка {column_name} добавлена")
                else:
                    logger.info(f"✅ Колонка {column_name} уже существует")
            
            # Проверяем результат
            logger.info("🔍 Проверяем структуру таблицы после миграции...")
            await cursor.execute("PRAGMA table_info(chat_activities)")
            columns = await cursor.fetchall()
            
            logger.info("📋 Структура таблицы chat_activities:")
            for col in columns:
                logger.info(f"  - {col[1]} ({col[2]})")
            
            logger.info("✅ Миграция успешно завершена!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        logger.error("🔄 Восстановление из резервной копии...")
        
        # Восстанавливаем из резервной копии
        if os.path.exists(BACKUP_PATH):
            with open(BACKUP_PATH, 'rb') as src:
                with open(DATABASE_PATH, 'wb') as dst:
                    dst.write(src.read())
            logger.info("✅ База данных восстановлена из резервной копии")
        
        return False

async def main():
    """Главная функция."""
    logger.info("🚀 Начинаем миграцию базы данных...")
    
    # Создаем необходимые директории
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    success = await migrate_database()
    
    if success:
        logger.info("🎉 Миграция завершена успешно!")
        logger.info("🔄 Перезапустите бота для применения изменений")
    else:
        logger.error("💥 Миграция завершилась с ошибками!")
        logger.error("📋 Проверьте логи для получения подробной информации")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
