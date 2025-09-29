#!/usr/bin/env python3
"""
Скрипт для проверки состояния бота.
"""

import asyncio
from loguru import logger
from app.core.database import get_db_session, init_database
from app.services.user_service import UserService
from app.services.payment_service import PaymentService

async def check_bot_status():
    """Проверка состояния бота и базы данных."""
    try:
        logger.info("🔍 Проверяем состояние бота...")
        
        # Инициализируем базу данных
        await init_database()
        logger.info("✅ База данных инициализирована")
        
        # Проверяем подключение к базе данных
        async with get_db_session() as session:
            user_service = UserService(session)
            payment_service = PaymentService(session)
            
            # Получаем статистику
            total_users = await user_service.get_total_users_count()
            active_users = await user_service.get_active_users_count()
            premium_users = await user_service.get_premium_users_count()
            
            total_payments = await payment_service.get_total_payments_count()
            successful_payments = await payment_service.get_successful_payments_count()
            
            logger.info("📊 Статистика бота:")
            logger.info(f"   👥 Всего пользователей: {total_users}")
            logger.info(f"   ✅ Активных пользователей: {active_users}")
            logger.info(f"   💎 Premium пользователей: {premium_users}")
            logger.info(f"   💳 Всего платежей: {total_payments}")
            logger.info(f"   ✅ Успешных платежей: {successful_payments}")
            
            # Проверяем последних пользователей
            recent_users = await user_service.get_recent_users(limit=5)
            logger.info("👥 Последние пользователи:")
            for user in recent_users:
                logger.info(f"   - {user.first_name} (@{user.username}) - {user.status}")
            
        logger.info("✅ Проверка состояния завершена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке состояния бота: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(check_bot_status())
