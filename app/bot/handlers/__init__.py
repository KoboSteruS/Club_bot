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
from .admin_dashboard import (
    admin_dashboard_handler,
    admin_users_handler,
    admin_payments_handler,
    admin_activity_handler,
    admin_refresh_handler,
    admin_broadcast_handler
)
from .group_info import group_info_handler


def register_handlers(application: Application) -> None:
    """Регистрация всех обработчиков."""
    try:
        # Команды
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("admin", admin_dashboard_handler))
        application.add_handler(CommandHandler("groupinfo", group_info_handler))
        
        # Callback queries
        application.add_handler(CallbackQueryHandler(main_handler, pattern="^(check_subscription|payment_options|about_club|back_to_start|subscription_confirmed|pay_|check_payment_)"))
        application.add_handler(CallbackQueryHandler(payment_handler, pattern="^payment"))
        application.add_handler(CallbackQueryHandler(report_handler, pattern="^report"))
        application.add_handler(CallbackQueryHandler(ritual_handler, pattern="^ritual"))
        application.add_handler(CallbackQueryHandler(goal_handler, pattern="^goal"))
        application.add_handler(CallbackQueryHandler(admin_handler, pattern="^admin"))
        
        # Админ-панель callback queries
        application.add_handler(CallbackQueryHandler(admin_dashboard_handler, pattern="^admin_dashboard"))
        application.add_handler(CallbackQueryHandler(admin_users_handler, pattern="^admin_users"))
        application.add_handler(CallbackQueryHandler(admin_payments_handler, pattern="^admin_payments"))
        application.add_handler(CallbackQueryHandler(admin_activity_handler, pattern="^admin_activity"))
        application.add_handler(CallbackQueryHandler(admin_refresh_handler, pattern="^admin_refresh"))
        application.add_handler(CallbackQueryHandler(admin_broadcast_handler, pattern="^admin_broadcast"))
        
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
    "admin_handler",
    "group_info_handler"
]
