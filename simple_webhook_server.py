#!/usr/bin/env python3
"""
Упрощенный webhook сервер для обработки CryptoBot уведомлений.
"""

import asyncio
import json
from aiohttp import web
from loguru import logger

async def cryptobot_webhook_handler(request):
    """Обработчик webhook от CryptoBot."""
    try:
        logger.info(f"Получен webhook от CryptoBot")
        
        # Читаем тело запроса
        body = await request.read()
        logger.info(f"Размер тела запроса: {len(body)} байт")
        
        # Парсим JSON
        try:
            webhook_data = json.loads(body.decode('utf-8'))
            logger.info(f"Данные webhook: {webhook_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return web.Response(status=400, text="Invalid JSON")
        
        # Обрабатываем webhook
        update_type = webhook_data.get('update_type')
        logger.info(f"Тип обновления: {update_type}")
        
        if update_type == "invoice_paid":
            payload = webhook_data.get('payload', {})
            invoice_id = payload.get('invoice_id')
            status = payload.get('status')
            
            logger.info(f"Оплачен счет {invoice_id} со статусом {status}")
            
            # Здесь должна быть логика обработки оплаты
            # Пока просто логируем
            
        return web.json_response({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return web.Response(status=500, text="Internal server error")

async def health_check(request):
    """Проверка здоровья сервера."""
    return web.json_response({"status": "healthy", "service": "CryptoBot Webhook"})

async def init_app():
    """Инициализация приложения."""
    app = web.Application()
    app.router.add_post('/webhook/cryptobot', cryptobot_webhook_handler)
    app.router.add_get('/health', health_check)
    return app

async def main():
    """Главная функция."""
    logger.info("🚀 Запуск CryptoBot webhook сервера...")
    
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()
    
    logger.info("✅ CryptoBot webhook сервер запущен на http://localhost:8000")
    logger.info("📋 CryptoBot webhook: http://localhost:8000/webhook/cryptobot")
    
    try:
        # Держим сервер запущенным
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 Сервер остановлен")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
