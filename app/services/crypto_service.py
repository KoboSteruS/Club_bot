"""
Сервис для работы с криптоплатежами через CryptoBot.

Содержит логику для создания счетов и обработки платежей в криптовалюте.
"""

import aiohttp
import hashlib
import hmac
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from loguru import logger

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings


class CryptoService:
    """Сервис для работы с CryptoBot API."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.api_url = "https://pay.crypt.bot/api"
        self.token = getattr(settings, 'CRYPTOBOT_TOKEN', '')
        
    async def create_invoice(self, amount: Decimal, currency: str = "RUB", 
                           description: str = "", user_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Создание счета для оплаты через CryptoBot.
        
        Args:
            amount: Сумма к оплате
            currency: Валюта (RUB, USD, EUR)
            description: Описание платежа
            user_id: ID пользователя Telegram
            
        Returns:
            Optional[Dict]: Данные созданного счета или None
        """
        try:
            if not self.token:
                logger.error("CRYPTOBOT_TOKEN не настроен")
                return None
                
            # Данные для создания счета
            payload = {
                "amount": str(amount),
                "fiat": currency,
                "description": description or "Оплата участия в клубе ОСНОВА ПУТИ",
                "hidden_message": f"Добро пожаловать в клуб! User ID: {user_id}",
                "paid_btn_name": "callback",
                "paid_btn_url": f"https://t.me/{settings.BOT_USERNAME}?start=paid_{user_id}",
                "start_parameter": f"invoice_{user_id}_{int(datetime.now().timestamp())}",
                "allow_comments": False,
                "allow_anonymous": True
            }
            
            headers = {
                "Crypto-Pay-API-Token": self.token,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/createInvoice",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            result = data.get("result", {})
                            logger.info(f"Создан счет CryptoBot: {result.get('invoice_id')}")
                            return result
                        else:
                            logger.error(f"Ошибка CryptoBot API: {data.get('error')}")
                    else:
                        logger.error(f"HTTP ошибка CryptoBot: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка создания счета CryptoBot: {e}")
            
        return None
    
    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о счете.
        
        Args:
            invoice_id: ID счета
            
        Returns:
            Optional[Dict]: Информация о счете или None
        """
        try:
            if not self.token:
                logger.error("CRYPTOBOT_TOKEN не настроен")
                return None
                
            headers = {
                "Crypto-Pay-API-Token": self.token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/getInvoice",
                    params={"invoice_id": invoice_id},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            return data.get("result")
                        else:
                            logger.error(f"Ошибка CryptoBot API: {data.get('error')}")
                    else:
                        logger.error(f"HTTP ошибка CryptoBot: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка получения счета CryptoBot: {e}")
            
        return None
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Проверка подписи webhook от CryptoBot.
        
        Args:
            body: Тело запроса
            signature: Подпись из заголовка
            
        Returns:
            bool: True если подпись верна
        """
        try:
            if not self.token:
                return False
                
            # Создаем подпись
            secret_key = hashlib.sha256(self.token.encode()).digest()
            expected_signature = hmac.new(secret_key, body, hashlib.sha256).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Ошибка проверки подписи CryptoBot: {e}")
            return False
    
    def get_payment_url(self, invoice_data: Dict[str, Any]) -> str:
        """
        Получение URL для оплаты.
        
        Args:
            invoice_data: Данные счета
            
        Returns:
            str: URL для оплаты
        """
        return invoice_data.get("pay_url", "")
    
    def get_tariff_info(self, tariff: str) -> Dict[str, Any]:
        """
        Получение информации о тарифе.
        
        Args:
            tariff: Тип тарифа (1month, 3months, subscription)
            
        Returns:
            Dict: Информация о тарифе
        """
        tariffs = {
            "1month": {
                "name": "1 месяц",
                "price": Decimal("2990"),
                "currency": "RUB",
                "duration_days": 30,
                "description": "Доступ к клубу ОСНОВА ПУТИ на 1 месяц"
            },
            "3months": {
                "name": "3 месяца",
                "price": Decimal("7990"),
                "currency": "RUB", 
                "duration_days": 90,
                "description": "Доступ к клубу ОСНОВА ПУТИ на 3 месяца (скидка 10%)"
            },
            "subscription": {
                "name": "Подписка",
                "price": Decimal("29990"),
                "currency": "RUB",
                "duration_days": 365,
                "description": "Безлимитный доступ к клубу ОСНОВА ПУТИ (скидка 15%)"
            }
        }
        
        return tariffs.get(tariff, tariffs["1month"])
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обработка webhook от CryptoBot.
        
        Args:
            webhook_data: Данные webhook
            
        Returns:
            bool: True если обработано успешно
        """
        try:
            update_type = webhook_data.get("update_type")
            
            if update_type == "invoice_paid":
                # Счет оплачен
                invoice = webhook_data.get("payload", {})
                invoice_id = invoice.get("invoice_id")
                status = invoice.get("status")
                
                if status == "paid":
                    logger.info(f"Получена оплата CryptoBot: {invoice_id}")
                    
                    # Извлекаем user_id из start_parameter
                    start_parameter = invoice.get("start_parameter", "")
                    if start_parameter.startswith("invoice_"):
                        parts = start_parameter.split("_")
                        if len(parts) >= 2:
                            user_id = parts[1]
                            
                            # Здесь нужно обновить статус пользователя в базе данных
                            # Это будет сделано в payment_service
                            return True
                            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook CryptoBot: {e}")
            return False
