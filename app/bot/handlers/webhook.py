"""
Обработчик webhook для CryptoBot.

Обрабатывает уведомления об оплаченных счетах от CryptoBot API.
"""

from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session
from app.services.crypto_service import CryptoService
from app.services.payment_service import PaymentService
from app.services.user_service import UserService
from app.services.telegram_service import TelegramService


async def process_cryptobot_webhook(webhook_data: Dict[str, Any]) -> bool:
    """
    Обработка webhook от CryptoBot согласно документации.
    
    Args:
        webhook_data: Данные webhook от CryptoBot
        
    Returns:
        bool: True если обработано успешно
    """
    try:
        update_type = webhook_data.get("update_type")
        
        if update_type == "invoice_paid":
            # Счет оплачен
            invoice = webhook_data.get("payload", {})
            invoice_id = str(invoice.get("invoice_id"))
            status = invoice.get("status")
            
            if status == "paid":
                logger.info(f"Получена оплата CryptoBot: {invoice_id}")
                
                async with get_db_session() as session:
                    payment_service = PaymentService(session)
                    user_service = UserService(session)
                    
                    # Находим платеж по внешнему ID
                    payment = await payment_service.get_payment_by_external_id(invoice_id)
                    if not payment:
                        logger.error(f"Платеж с ID {invoice_id} не найден в базе данных")
                        return False
                    
                    # Обновляем статус платежа
                    from app.schemas.payment import PaymentUpdate
                    await payment_service.update_payment(str(payment.id), PaymentUpdate(
                        status="completed",
                        paid_at=invoice.get("paid_at")
                    ))
                    
                    # Активируем подписку пользователя
                    # payment.user_id содержит UUID пользователя, получаем пользователя по UUID
                    db_user = await user_service.get_user(payment.user_id)
                    if db_user:
                        from datetime import datetime, timedelta
                        from app.schemas.user import UserUpdate
                        
                        # Определяем длительность подписки
                        tariff_type = payment.tariff_type or "1month"
                        duration_map = {"1month": 30, "3months": 90, "subscription": 365}
                        duration_days = duration_map.get(tariff_type, 30)
                        
                        subscription_end = datetime.utcnow() + timedelta(days=duration_days)
                        
                        await user_service.update_user(str(db_user.id), UserUpdate(
                            is_premium=True,
                            subscription_end=subscription_end
                        ))
                        
                        logger.info(f"Активирована подписка для пользователя {db_user.telegram_id} до {subscription_end}")
                        
                        # Отправляем уведомление пользователю о успешной оплате
                        try:
                            from app.services.telegram_service import TelegramService
                            telegram_service = TelegramService()
                            
                            # Отправляем сообщение об успешной активации
                            success_message = (
                                f"🎉 **Поздравляем!**\n\n"
                                f"✅ Ваша подписка успешно активирована!\n"
                                f"📅 Действует до: {subscription_end.strftime('%d.%m.%Y')}\n"
                                f"💎 Тариф: {tariff_type}\n\n"
                                f"Добро пожаловать в клуб **ОСНОВА ПУТИ**! 🚀"
                            )
                            
                            await telegram_service.send_message(
                                user_id=db_user.telegram_id,
                                message=success_message
                            )
                            
                            logger.info(f"Отправлено уведомление об активации подписки пользователю {db_user.telegram_id}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка отправки уведомления пользователю {db_user.telegram_id}: {e}")
                        
                        return True
                    else:
                        logger.error(f"Пользователь с ID {payment.user_id} не найден")
                        return False
                        
        return False
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook CryptoBot: {e}")
        return False


async def handle_cryptobot_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик webhook от CryptoBot для Telegram бота.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        # Этот обработчик будет вызван через HTTP endpoint
        # Пока что просто логируем
        logger.info("Получен webhook от CryptoBot")
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")


# Функция для тестирования CryptoBot API
async def test_cryptobot_connection() -> bool:
    """
    Тестирование подключения к CryptoBot API.
    
    Returns:
        bool: True если подключение работает
    """
    try:
        crypto_service = CryptoService()
        
        # Создаем тестовый счет на 1 USDT
        test_invoice = await crypto_service.create_invoice(
            amount=1.0,
            asset="USDT",
            description="Тест подключения к CryptoBot",
            user_id=123456
        )
        
        if test_invoice:
            logger.info(f"✅ CryptoBot подключен! Тестовый счет: {test_invoice.get('invoice_id')}")
            return True
        else:
            logger.error("❌ CryptoBot не отвечает")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к CryptoBot: {e}")
        return False
