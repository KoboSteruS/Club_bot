"""
Настройки базы данных с использованием SQLAlchemy.

Содержит конфигурацию подключения к базе данных и сессии.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

import sys
from pathlib import Path

# Добавляем путь к конфигурации
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


# Создание асинхронного движка базы данных
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение сессии базы данных.
    
    Yields:
        AsyncSession: Асинхронная сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка в сессии базы данных: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """
    Получение сессии базы данных (контекстный менеджер).
    
    Yields:
        AsyncSession: Асинхронная сессия базы данных
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка в сессии базы данных: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Инициализация базы данных."""
    try:
        # Импортируем все модели для регистрации в метаданных
        from app.models import (
            User, Payment, Ritual, UserRitual, RitualResponse, Report, Goal,
            ChatActivity, UserActivity, ActivitySummary, WeeklyReport
        )
        
        async with engine.begin() as conn:
            # Создание всех таблиц
            await conn.run_sync(Base.metadata.create_all)
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


async def close_database() -> None:
    """Закрытие соединения с базой данных."""
    await engine.dispose()
    logger.info("Соединение с базой данных закрыто")
