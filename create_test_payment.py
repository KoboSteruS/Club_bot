#!/usr/bin/env python3
"""
Создание тестового платежа для проверки webhook.
"""

import asyncio
from datetime import datetime, timedelta
from loguru import logger

from app.core.database import init_database, get_db_session
from app.services.user_service import UserService
from app.services.payment_service import PaymentService
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.payment import PaymentCreate

async def create_test_payment():
    """Создание тестового платежа для проверки webhook."""
    
    # Инициализируем базу данных
    await init_database()
    
    async with get_db_session() as session:
        user_service = UserService(session)
        payment_service = PaymentService(session)
        
        # Создаем тестового пользователя
        test_user_data = UserCreate(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        
        # Проверяем, существует ли пользователь
        existing_user = await user_service.get_user_by_telegram_id(123456789)
        if existing_user:
            logger.info(f"Пользователь уже существует: {existing_user.id}")
            user = existing_user
        else:
            user = await user_service.create_user(test_user_data)
            logger.info(f"Создан тестовый пользователь: {user.id}")
        
        # Создаем тестовый платеж
        test_payment_data = PaymentCreate(
            user_id=str(user.id),
            amount=0.10,
            currency="USDT",
            description="Тестовый платеж для webhook",
            tariff_type="1month",
            external_id="12345678"  # ID для webhook теста
        )
        
        # Проверяем, существует ли платеж
        existing_payment = await payment_service.get_payment_by_external_id("12345678")
        if existing_payment:
            logger.info(f"Платеж уже существует: {existing_payment.id}")
        else:
            payment = await payment_service.create_payment(test_payment_data)
            logger.info(f"Создан тестовый платеж: {payment.id}")
        
        logger.info("✅ Тестовый платеж создан успешно!")

if __name__ == "__main__":
    asyncio.run(create_test_payment())

