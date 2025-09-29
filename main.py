"""
Основной файл для запуска ClubBot.
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from app.core.database import init_database, get_db_session
from app.bot.bot import TelegramBot
from config.settings import settings
from app.core.logging import setup_logging_from_settings


async def main():
    """Основная функция запуска ClubBot."""
    try:
        logger.info("🚀 Запуск ClubBot...")
        logger.info(f"📱 Название: {settings.BOT_NAME}")
        logger.info(f"🔧 Режим отладки: {settings.DEBUG}")
        
        # Создаем базу данных
        await init_database()
        logger.info("✅ База данных создана/обновлена")
        
        # Создаем и запускаем бота
        bot = TelegramBot()
        
        # Получаем информацию о боте
        try:
            bot_info = await bot.get_me()
            username = bot_info.get("username", "неизвестно")
            logger.info(f"🤖 Бот запущен: @{username}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить информацию о боте: {e}")
        
        # Запускаем бота
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        logger.info("👋 ClubBot остановлен")


if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging_from_settings()
    
    # Запускаем бота
    asyncio.run(main())