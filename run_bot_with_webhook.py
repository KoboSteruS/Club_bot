#!/usr/bin/env python3
"""
Запуск бота вместе с webhook сервером.

Этот скрипт запускает:
1. Telegram бота для обработки команд пользователей
2. HTTP сервер для обработки webhook'ов от CryptoBot
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.database import init_database
from app.bot.bot import TelegramBot
from app.webhook_server import WebhookServer
from loguru import logger


class BotWithWebhookRunner:
    """Класс для запуска бота с webhook сервером."""
    
    def __init__(self):
        self.settings = get_settings()
        self.bot: Optional[TelegramBot] = None
        self.webhook_server: Optional[WebhookServer] = None
        self.running = False
        
    async def start(self) -> None:
        """Запуск бота и webhook сервера."""
        try:
            logger.info("🚀 Запуск ClubBot с Webhook сервером...")
            logger.info(f"📱 Название: {self.settings.BOT_NAME}")
            logger.info(f"🔧 Режим отладки: {self.settings.DEBUG}")
            
            # Инициализация базы данных
            await init_database()
            logger.info("✅ База данных создана/обновлена")
            
            # Создание и запуск Telegram бота
            self.bot = TelegramBot()
            await self.bot.start()
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            bot_username = bot_info.get("username", "неизвестно")
            logger.info(f"🤖 Telegram бот запущен: @{bot_username}")
            
            # Создание и запуск webhook сервера
            self.webhook_server = WebhookServer(
                host=self.settings.WEBHOOK_HOST,
                port=self.settings.WEBHOOK_PORT
            )
            await self.webhook_server.start()
            
            self.running = True
            logger.info("🎉 Все сервисы запущены успешно!")
            
            # Выводим информацию о webhook URL
            if self.settings.WEBHOOK_URL:
                logger.info(f"🔗 Внешний webhook URL: {self.settings.WEBHOOK_URL}/webhook/cryptobot")
            else:
                logger.info(f"🔗 Локальный webhook URL: http://localhost:{self.settings.WEBHOOK_PORT}/webhook/cryptobot")
                logger.warning("⚠️  Для production установите WEBHOOK_URL в настройках!")
            
            # Ждем сигнал остановки
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"💥 Критическая ошибка при запуске: {e}")
            raise
            
    async def stop(self) -> None:
        """Остановка всех сервисов."""
        logger.info("🛑 Остановка сервисов...")
        self.running = False
        
        # Остановка Telegram бота
        if self.bot:
            await self.bot.stop()
            logger.info("✅ Telegram бот остановлен")
            
        # Остановка webhook сервера  
        if self.webhook_server:
            await self.webhook_server.stop()
            logger.info("✅ Webhook сервер остановлен")
            
        logger.info("👋 Все сервисы остановлены")
        
    def handle_signal(self, signum, frame):
        """Обработчик сигналов остановки."""
        logger.info(f"Получен сигнал {signum}, остановка...")
        asyncio.create_task(self.stop())


async def main():
    """Главная функция."""
    runner = BotWithWebhookRunner()
    
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, runner.handle_signal)
    signal.signal(signal.SIGTERM, runner.handle_signal)
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        logger.info("👋 Получен сигнал остановки от пользователя")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        await runner.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 ClubBot завершен")
    except Exception as e:
        logger.error(f"💥 Ошибка запуска: {e}")
        sys.exit(1)
