#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы логирования.
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from app.core.logging import setup_logging_from_settings


def test_logging():
    """Тестирование системы логирования."""
    
    print("🔧 Настройка логирования...")
    setup_logging_from_settings()
    
    print("📝 Тестирование различных уровней логирования...")
    
    # Тестируем различные уровни логирования
    logger.debug("🐛 Это DEBUG сообщение - детальная информация для отладки")
    logger.info("ℹ️ Это INFO сообщение - общая информация о работе")
    logger.warning("⚠️ Это WARNING сообщение - предупреждение о потенциальной проблеме")
    logger.error("❌ Это ERROR сообщение - ошибка в работе приложения")
    logger.critical("💥 Это CRITICAL сообщение - критическая ошибка")
    
    # Тестируем исключение
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("🔥 Исключение с полным traceback")
    
    # Тестируем структурированные данные
    user_data = {
        "id": 12345,
        "username": "test_user",
        "action": "login",
        "timestamp": "2025-09-29 12:00:00"
    }
    logger.info(f"👤 Действие пользователя: {user_data}")
    
    # Тестируем форматирование
    logger.info("📊 Статистика: пользователей={users}, активных={active}", 
                users=100, active=75)
    
    print("\n✅ Тестирование завершено!")
    print("📁 Проверьте файлы:")
    print("   - logs/clubbot.log (все сообщения)")
    print("   - logs/clubbot_errors.log (только ошибки)")


if __name__ == "__main__":
    test_logging()
