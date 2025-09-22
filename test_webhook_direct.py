#!/usr/bin/env python3
"""
Прямой тест webhook'а CryptoBot без создания платежа в БД.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from config.settings import get_settings

async def test_webhook_direct():
    """Прямое тестирование webhook endpoint."""
    settings = get_settings()
    
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

async def test_health():
    """Тестирование health endpoint."""
    settings = get_settings()
    health_url = f"http://localhost:{settings.WEBHOOK_PORT}/health"
    
    print(f"🏥 Проверяем health endpoint: {health_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                print(f"📡 Статус: {response.status}")
                response_text = await response.text()
                print(f"📄 Ответ: {response_text}")
                
                if response.status == 200:
                    print("✅ Health endpoint работает!")
                else:
                    print("❌ Health endpoint недоступен")
                    
    except Exception as e:
        print(f"❌ Ошибка при проверке health: {e}")

async def main():
    """Основная функция тестирования."""
    print("🚀 Начинаем прямое тестирование webhook сервера...\n")
    
    # Сначала проверяем health
    await test_health()
    print("\n" + "="*50 + "\n")
    
    # Затем тестируем webhook
    await test_webhook_direct()
    
    print("\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
