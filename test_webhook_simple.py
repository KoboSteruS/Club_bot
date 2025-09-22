#!/usr/bin/env python3
"""
Простой тест webhook'а CryptoBot.
Создает тестовый платеж в БД и отправляет webhook.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from config.settings import get_settings
from app.core.database import get_db_session
from app.services.payment_service import PaymentService
from app.services.user_service import UserService
from app.schemas.payment import PaymentCreate

async def create_test_payment():
    """Создание тестового платежа в базе данных."""
    settings = get_settings()
    
    async with get_db_session() as session:
        payment_service = PaymentService(session)
        user_service = UserService(session)
        
        # Находим пользователя по Telegram ID
        user = await user_service.get_user_by_telegram_id(1670311707)
        if not user:
            print("❌ Пользователь не найден в базе данных")
            return None
            
        # Создаем тестовый платеж
        payment_data = PaymentCreate(
            user_id=str(user.id),
            amount=0.1,
            currency="USDT",
            description="Тестовый платеж для webhook",
            external_id="test_invoice_123",
            tariff_type="monthly"
        )
        
        payment = await payment_service.create_payment(payment_data)
        print(f"✅ Создан тестовый платеж: {payment.id}")
        return payment

async def test_webhook():
    """Тестирование webhook endpoint."""
    settings = get_settings()
    
    # Сначала создаем тестовый платеж
    payment = await create_test_payment()
    if not payment:
        return
    
    # Тестовые данные платежа в формате CryptoBot
    test_payment_data = {
        "update_id": 123456789,
        "update_type": "invoice_paid",
        "request_date": datetime.now().isoformat(),
        "payload": {
            "invoice_id": "test_invoice_123",
            "status": "paid",
            "asset": "USDT",
            "amount": "0.1",
            "order_description": "Тестовый платеж для клуба ОСНОВА ПУТИ",
            "created_at": datetime.now().isoformat(),
            "paid_at": datetime.now().isoformat(),
            "payload": "monthly"
        }
    }
    
    webhook_url = f"http://localhost:{settings.WEBHOOK_PORT}/webhook/cryptobot"
    
    print(f"🧪 Тестируем webhook: {webhook_url}")
    print(f"📊 Данные платежа:")
    print(json.dumps(test_payment_data, indent=2, ensure_ascii=False))
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=test_payment_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"\n📡 Статус ответа: {response.status}")
                response_text = await response.text()
                print(f"📄 Ответ сервера: {response_text}")
                
                if response.status == 200:
                    print("✅ Webhook работает корректно!")
                else:
                    print("❌ Webhook вернул ошибку")
                    
    except Exception as e:
        print(f"❌ Ошибка при тестировании webhook: {e}")

async def main():
    """Основная функция тестирования."""
    print("🚀 Начинаем тестирование webhook с тестовым платежом...\n")
    
    await test_webhook()
    
    print("\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
