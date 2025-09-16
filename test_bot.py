#!/usr/bin/env python3
"""
Тестовый файл для проверки ClubBot.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from config.settings import settings

async def test_bot():
    """Тестирование бота."""
    try:
        logger.info("🚀 Тестирование ClubBot...")
        logger.info(f"📱 Название: {settings.BOT_NAME}")
        logger.info(f"🔧 Режим отладки: {settings.DEBUG}")
        logger.info(f"🔑 Токен: {settings.BOT_TOKEN[:10]}...")
        logger.info(f"🗄️ База данных: {settings.DATABASE_URL}")
        
        # Тестируем импорт бота
        from app.bot.bot import TelegramBot
        logger.info("✅ Импорт TelegramBot успешен")
        
        # Тестируем создание бота
        bot = TelegramBot()
        logger.info("✅ Создание TelegramBot успешно")
        
        # Тестируем получение информации о боте
        try:
            bot_info = await bot.get_me()
            logger.info(f"🤖 Бот: @{bot_info.username}")
            logger.info(f"📝 Имя: {bot_info.first_name}")
            logger.info(f"🆔 ID: {bot_info.id}")
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о боте: {e}")
            return
        
        logger.info("✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Настраиваем логирование
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Запускаем тест
    asyncio.run(test_bot())



