#!/usr/bin/env python3
"""
Простой тест webhook сервера.
"""

import asyncio
import aiohttp
import json
from loguru import logger

async def test_webhook():
    """Тестирование webhook сервера."""
    
    # URL webhook сервера
    webhook_url = "http://localhost:8000/webhook/cryptobot"
    
    # Тестовые данные webhook от CryptoBot
    test_data = {
        "update_type": "invoice_paid",
        "payload": {
            "invoice_id": "12345678",
            "status": "paid",
            "paid_at": "2025-09-26T10:00:00Z",
            "amount": "0.10",
            "asset": "USDT"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Отправляем POST запрос на webhook
            async with session.post(
                webhook_url,
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                logger.info(f"Статус ответа: {response.status}")
                response_text = await response.text()
                logger.info(f"Ответ сервера: {response_text}")
                
                if response.status == 200:
                    logger.info("✅ Webhook работает корректно!")
                else:
                    logger.error(f"❌ Webhook вернул ошибку: {response.status}")
                    
    except aiohttp.ClientConnectorError:
        logger.error("❌ Не удалось подключиться к webhook серверу. Убедитесь, что сервер запущен на localhost:8000")
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании webhook: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())

