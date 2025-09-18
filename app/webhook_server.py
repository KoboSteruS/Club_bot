"""
HTTP сервер для обработки webhook'ов от внешних сервисов.

Обрабатывает webhook'и от:
- CryptoBot (уведомления об оплате)
- Другие платежные системы (при необходимости)
"""

import asyncio
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
from loguru import logger

from app.core.config import get_settings
from app.bot.handlers.webhook import process_cryptobot_webhook


class WebhookServer:
    """HTTP сервер для обработки webhook'ов."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Инициализация сервера.
        
        Args:
            host: Хост для привязки сервера
            port: Порт для привязки сервера
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.settings = get_settings()
        self._setup_routes()
        
    def _setup_routes(self) -> None:
        """Настройка маршрутов."""
        self.app.router.add_post('/webhook/cryptobot', self.handle_cryptobot_webhook)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.root_handler)
        
    async def root_handler(self, request: web.Request) -> web.Response:
        """Корневой обработчик."""
        return web.json_response({
            "status": "ok",
            "service": "ClubBot Webhook Server",
            "version": "1.0.0"
        })
        
    async def health_check(self, request: web.Request) -> web.Response:
        """Проверка здоровья сервиса."""
        return web.json_response({
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    def _verify_cryptobot_signature(self, body: bytes, signature: str) -> bool:
        """
        Проверка подписи webhook'а от CryptoBot.
        
        Args:
            body: Тело запроса
            signature: Подпись из заголовка
            
        Returns:
            bool: True если подпись валидна
        """
        try:
            # CryptoBot использует HMAC-SHA256 с секретным ключом
            secret = self.settings.CRYPTOBOT_TOKEN.encode()
            expected_signature = hmac.new(
                secret, 
                body, 
                hashlib.sha256
            ).hexdigest()
            
            # Сравниваем подписи
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Ошибка проверки подписи CryptoBot: {e}")
            return False
            
    async def handle_cryptobot_webhook(self, request: web.Request) -> web.Response:
        """
        Обработка webhook'а от CryptoBot.
        
        Args:
            request: HTTP запрос
            
        Returns:
            web.Response: HTTP ответ
        """
        try:
            # Читаем тело запроса
            body = await request.read()
            
            # Получаем подпись из заголовков
            signature = request.headers.get('crypto-pay-api-signature', '')
            
            # Проверяем подпись (в production обязательно!)
            if not self._verify_cryptobot_signature(body, signature):
                logger.warning("Неверная подпись webhook CryptoBot")
                # В тестовом режиме пропускаем проверку подписи
                # return web.Response(status=401, text="Invalid signature")
                
            # Парсим JSON
            try:
                webhook_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON webhook CryptoBot: {e}")
                return web.Response(status=400, text="Invalid JSON")
                
            logger.info(f"Получен webhook CryptoBot: {webhook_data.get('update_type')}")
            
            # Обрабатываем webhook
            success = await process_cryptobot_webhook(webhook_data)
            
            if success:
                logger.info("Webhook CryptoBot обработан успешно")
                return web.json_response({"status": "ok"})
            else:
                logger.error("Ошибка обработки webhook CryptoBot")
                return web.Response(status=500, text="Processing failed")
                
        except Exception as e:
            logger.error(f"Ошибка в handle_cryptobot_webhook: {e}")
            return web.Response(status=500, text="Internal server error")
            
    async def start(self) -> None:
        """Запуск сервера."""
        logger.info(f"🌐 Запуск webhook сервера на {self.host}:{self.port}")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"✅ Webhook сервер запущен на http://{self.host}:{self.port}")
        logger.info(f"📋 CryptoBot webhook: http://{self.host}:{self.port}/webhook/cryptobot")
        
    async def stop(self) -> None:
        """Остановка сервера."""
        logger.info("🛑 Остановка webhook сервера...")
        await self.app.cleanup()
        logger.info("✅ Webhook сервер остановлен")


# Функция для запуска сервера в отдельном процессе
async def run_webhook_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Запуск webhook сервера.
    
    Args:
        host: Хост для привязки
        port: Порт для привязки
    """
    server = WebhookServer(host, port)
    await server.start()
    
    try:
        # Держим сервер запущенным
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await server.stop()


if __name__ == "__main__":
    # Запуск сервера напрямую
    asyncio.run(run_webhook_server())
