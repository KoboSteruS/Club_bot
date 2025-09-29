#!/usr/bin/env python3
"""
Простой тестовый webhook сервер для проверки.
"""

import asyncio
from aiohttp import web
from loguru import logger

async def test_handler(request):
    """Тестовый обработчик."""
    logger.info(f"Получен запрос: {request.method} {request.path}")
    data = await request.json() if request.content_type == 'application/json' else {}
    logger.info(f"Данные: {data}")
    return web.json_response({"status": "ok", "message": "Test webhook received"})

async def health_check(request):
    """Проверка здоровья сервера."""
    return web.json_response({"status": "healthy"})

async def init_app():
    """Инициализация приложения."""
    app = web.Application()
    app.router.add_post('/webhook/test', test_handler)
    app.router.add_get('/health', health_check)
    return app

async def main():
    """Главная функция."""
    logger.info("🚀 Запуск тестового webhook сервера...")
    
    app = await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()
    
    logger.info("✅ Тестовый webhook сервер запущен на http://localhost:8000")
    
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
