#!/usr/bin/env python3
"""
Скрипт для очистки кэша подписки.
"""

import asyncio
from loguru import logger
from telegram import Bot
from config.settings import get_settings
from app.services.telegram_service import TelegramService

async def clear_cache():
    """Очистка кэша подписки."""
    try:
        settings = get_settings()
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        telegram_service = TelegramService(bot)
        
        logger.info("🧹 Очищаем кэш подписки...")
        telegram_service.clear_subscription_cache()
        logger.info("✅ Кэш подписки очищен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке кэша: {e}")

if __name__ == "__main__":
    asyncio.run(clear_cache())
