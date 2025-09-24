"""
Декораторы для проверки подписки и платежей.
"""

from functools import wraps
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session
from app.services import UserService, TelegramService


def require_subscription(func):
    """
    Декоратор для проверки подписки на канал.
    Если пользователь не подписан, отправляет сообщение о необходимости подписки.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            user = update.effective_user
            if not user:
                logger.error("Не удалось получить данные пользователя")
                return
            
            # Проверяем подписку
            telegram_service = TelegramService(context.bot)
            is_subscribed = await telegram_service.check_user_subscription(user.id)
            
            if not is_subscribed:
                await telegram_service.send_subscription_required_message(user.id)
                return
            
            # Если подписан, выполняем оригинальную функцию
            return await func(update, context, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Ошибка в декораторе require_subscription: {e}")
            return
    
    return wrapper


def require_payment(func):
    """
    Декоратор для проверки активной подписки (оплаты).
    Если у пользователя нет активной подписки, отправляет сообщение о необходимости оплаты.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            user = update.effective_user
            if not user:
                logger.error("Не удалось получить данные пользователя")
                return
            
            async with get_db_session() as session:
                user_service = UserService(session)
                db_user = await user_service.get_user_by_telegram_id(user.id)
                
                if not db_user:
                    # Пользователь не найден, отправляем приветствие
                    from app.bot.handlers.start import start_command_handler
                    return await start_command_handler(update, context)
                
                # Проверяем активную подписку
                if not db_user.subscription_until or db_user.subscription_until <= datetime.now():
                    # Нет активной подписки
                    telegram_service = TelegramService(context.bot)
                    await telegram_service.send_payment_required_message(user.id)
                    return
                
                # Если есть активная подписка, выполняем оригинальную функцию
                return await func(update, context, *args, **kwargs)
                
        except Exception as e:
            logger.error(f"Ошибка в декораторе require_payment: {e}")
            return
    
    return wrapper
