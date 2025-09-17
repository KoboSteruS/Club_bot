"""
Обработчики для ClubBot.
"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from loguru import logger

from .start import start_handler
from .main import main_handler
from .payment import payment_handler
from .reports import report_handler
from .rituals import ritual_handler
from .goals import goal_handler
from .admin_simple import admin_handler


def register_handlers(application: Application) -> None:
    """Регистрация всех обработчиков."""
    try:
        # Команды
        application.add_handler(CommandHandler("start", start_handler))
        
        # Callback queries
        application.add_handler(CallbackQueryHandler(main_handler, pattern="^(check_subscription|payment_options|about_club|back_to_start|subscription_confirmed|pay_|check_payment_)"))
        application.add_handler(CallbackQueryHandler(payment_handler, pattern="^payment"))
        application.add_handler(CallbackQueryHandler(report_handler, pattern="^report"))
        application.add_handler(CallbackQueryHandler(ritual_handler, pattern="^ritual"))
        application.add_handler(CallbackQueryHandler(goal_handler, pattern="^goal"))
        application.add_handler(CallbackQueryHandler(admin_handler, pattern="^admin"))
        
        # Сообщения
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_handler))
        
        logger.info("✅ Все обработчики зарегистрированы")
        
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации обработчиков: {e}")
        raise


__all__ = [
    "register_handlers",
    "start_handler",
    "main_handler",
    "payment_handler", 
    "report_handler",
    "ritual_handler",
    "goal_handler",
    "admin_handler"
]
