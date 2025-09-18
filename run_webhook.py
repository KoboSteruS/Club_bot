#!/usr/bin/env python3
"""
Запуск webhook сервера для обработки уведомлений от CryptoBot.

Этот сервер должен быть доступен из интернета для получения webhook'ов.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from app.webhook_server import run_webhook_server
from app.core.config import get_settings
from loguru import logger


async def main():
    """Главная функция."""
    settings = get_settings()
    
    logger.info("🚀 Запуск Webhook сервера ClubBot...")
    logger.info(f"🔧 Режим отладки: {settings.DEBUG}")
    
    # Настройки сервера
    host = "0.0.0.0"  # Слушаем на всех интерфейсах
    port = 8000       # Порт по умолчанию
    
    try:
        await run_webhook_server(host, port)
    except KeyboardInterrupt:
        logger.info("👋 Webhook сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка webhook сервера: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Webhook сервер завершен")
    except Exception as e:
        logger.error(f"💥 Ошибка запуска: {e}")
        sys.exit(1)
