#!/usr/bin/env python3
"""
Тестовый скрипт для проверки webhook'а CryptoBot.
Отправляет тестовое уведомление об оплате.
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from config.settings import get_settings

async def test_webhook():
    """Тестирование webhook endpoint."""
    settings = get_settings()
    
    # Тестовые данные платежа в формате CryptoBot
    test_payment_data = {
        "update_id": 123456789,
        "update_type": "invoice_paid",
        "request_date": datetime.now().isoformat(),
        "payload": {
            "invoice_id": "test_invoice_123",
            "status": "paid",
            "hash": "test_hash_123",
            "currency_type": "crypto",
            "asset": "USDT",
            "amount": "0.1",
            "paid_asset": "USDT",
            "paid_amount": "0.1",
            "paid_fiat_value": "0.1",
            "fiat": "USD",
            "fee_asset": "USDT",
            "fee_amount": "0.001",
            "fee_fiat_value": "0.001",
            "order_id": "test_order_123",
            "order_description": "Тестовый платеж для клуба ОСНОВА ПУТИ",
            "success_asset": "USDT",
            "success_amount": "0.099",
            "success_fiat_value": "0.099",
            "created_at": datetime.now().isoformat(),
            "paid_at": datetime.now().isoformat(),
            "allow_comments": True,
            "allow_anonymous": True,
            "expiration_date": None,
            "paid_anonymously": False,
            "comment": "",
            "hidden_message": "",
            "payload": "monthly_subscription",
            "paid_btn_name": "callback",
            "paid_btn_url": "",
            "invoice_url": "https://t.me/CryptoBot?start=test_invoice_123"
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
    print("🚀 Начинаем тестирование webhook сервера...\n")
    
    # Сначала проверяем health
    await test_health()
    print("\n" + "="*50 + "\n")
    
    # Затем тестируем webhook
    await test_webhook()
    
    print("\n🎯 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
