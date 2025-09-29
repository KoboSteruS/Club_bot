"""
Централизованная настройка логирования для ClubBot.

Настраивает loguru для записи логов в консоль и файлы.
"""

import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional

from config.settings import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_error_file: Optional[str] = None,
    log_format: Optional[str] = None,
    log_rotation: Optional[str] = None,
    log_retention: Optional[str] = None,
    debug: Optional[bool] = None
) -> None:
    """
    Настройка логирования для приложения.
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к основному файлу логов
        log_error_file: Путь к файлу логов ошибок
        log_format: Формат записи логов
        log_rotation: Период ротации логов
        log_retention: Время хранения логов
        debug: Режим отладки
    """
    # Получаем настройки
    settings = get_settings()
    
    # Используем переданные параметры или значения по умолчанию из настроек
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    log_error_file = log_error_file or settings.LOG_ERROR_FILE
    log_format = log_format or settings.LOG_FORMAT
    log_rotation = log_rotation or settings.LOG_ROTATION
    log_retention = log_retention or settings.LOG_RETENTION
    debug = debug if debug is not None else settings.DEBUG
    
    # Удаляем все существующие обработчики
    logger.remove()
    
    # Настройка для консоли
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        level=log_level,
        format=console_format,
        colorize=True,
        backtrace=debug,
        diagnose=debug
    )
    
    # Создаем директорию для логов если она не существует
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Основной файл логов (все уровни)
        logger.add(
            log_file,
            level="DEBUG",  # Записываем все уровни в основной файл
            format=log_format,
            rotation=log_rotation,
            retention=log_retention,
            compression="zip",
            backtrace=debug,
            diagnose=debug,
            encoding="utf-8-sig"
        )
    
    # Создаем директорию для логов ошибок если она не существует
    if log_error_file:
        error_log_dir = Path(log_error_file).parent
        error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Файл только для ошибок (ERROR и CRITICAL)
        logger.add(
            log_error_file,
            level="ERROR",  # Только ошибки и критические ошибки
            format=log_format,
            rotation=log_rotation,
            retention=log_retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
            encoding="utf-8-sig"
        )
    
    # Логируем информацию о настройке
    logger.info("🔧 Логирование настроено:")
    logger.info(f"   📊 Уровень: {log_level}")
    logger.info(f"   📁 Основной файл: {log_file}")
    logger.info(f"   ❌ Файл ошибок: {log_error_file}")
    logger.info(f"   🔄 Ротация: {log_rotation}")
    logger.info(f"   🗂️ Хранение: {log_retention}")
    logger.info(f"   🐛 Отладка: {'включена' if debug else 'выключена'}")


def get_logger():
    """
    Получить настроенный логгер.
    
    Returns:
        Настроенный экземпляр loguru logger
    """
    return logger


# Функция для быстрой настройки логирования из настроек
def setup_logging_from_settings() -> None:
    """Настройка логирования из настроек приложения."""
    setup_logging()
