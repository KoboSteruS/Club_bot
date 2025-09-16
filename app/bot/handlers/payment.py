"""
Обработчики для платежей.

Обрабатывает команды и callback'и связанные с платежами.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_database
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config.settings import settings
from app.services import UserService, PaymentService, TelegramService
from app.schemas.payment import PaymentCreate


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /payment (временно отключен).
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        await update.message.reply_text(
            "💳 <b>Оплата временно недоступна</b>\n\n"
            "🚧 Функция оплаты находится в разработке.\n"
            "Для получения доступа к клубу обратитесь к администратору.\n\n"
            "📝 В данный момент доступны:\n"
            "• /start - Главное меню\n"
            "• Проверка подписки на канал\n"
            "• Ежедневные отчеты\n"
            "• Еженедельные цели\n"
            "• Анализ активности",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки команды /payment: {e}")


async def payment_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик callback'ов для платежей (временно отключен).
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "💳 Функция оплаты временно недоступна.\n"
                "Обратитесь к администратору для получения доступа."
            )
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback'а платежа: {e}")
