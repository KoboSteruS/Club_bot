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
from .admin_dashboard import (
    admin_dashboard_handler,
    admin_users_handler,
    admin_access_handler,
    admin_give_access_all_handler,
    admin_give_access_by_id_handler,
    admin_revoke_access_by_id_handler,
    handle_user_id_input,
    handle_revoke_user_id_input,
    admin_activity_handler,
    admin_activity_by_chats_handler,
    admin_chat_activity_handler,
    admin_refresh_handler,
    admin_broadcast_handler,
    admin_management_handler,
    admin_add_admin_handler,
    admin_remove_admin_handler,
    handle_admin_id_input,
    admin_check_subscriptions_handler,
    admin_send_to_group_handler,
    handle_group_message_input
)
from .group_info import group_info_handler
from .group_activity import (
    group_message_handler_func,
    group_member_handler_func,
    group_left_member_handler_func
)


def register_handlers(application: Application) -> None:
    """Регистрация всех обработчиков."""
    try:
        # Команды
        application.add_handler(CommandHandler("start", start_handler))
        application.add_handler(CommandHandler("admin", admin_dashboard_handler))
        application.add_handler(CommandHandler("groupinfo", group_info_handler))
        
        # Callback queries
        application.add_handler(CallbackQueryHandler(main_handler, pattern="^(check_subscription|payment_options|about_club|back_to_start|subscription_confirmed|pay_|check_payment_|choose_payment_method|confirm_card_payment|confirm_sbp_payment)"))
        application.add_handler(CallbackQueryHandler(payment_handler, pattern="^payment"))
        application.add_handler(CallbackQueryHandler(report_handler, pattern="^report"))
        application.add_handler(CallbackQueryHandler(ritual_handler, pattern="^ritual_[^s]"))
        application.add_handler(CallbackQueryHandler(goal_handler, pattern="^goal"))
        
        # Админ-панель callback queries
        application.add_handler(CallbackQueryHandler(admin_dashboard_handler, pattern="^admin_dashboard"))
        application.add_handler(CallbackQueryHandler(admin_users_handler, pattern="^admin_users.*"))
        application.add_handler(CallbackQueryHandler(admin_access_handler, pattern="^admin_access"))
        application.add_handler(CallbackQueryHandler(admin_give_access_all_handler, pattern="^admin_give_access_all"))
        application.add_handler(CallbackQueryHandler(admin_give_access_by_id_handler, pattern="^admin_give_access_by_id"))
        application.add_handler(CallbackQueryHandler(admin_revoke_access_by_id_handler, pattern="^admin_revoke_access_by_id"))
        application.add_handler(CallbackQueryHandler(admin_management_handler, pattern="^admin_management"))
        application.add_handler(CallbackQueryHandler(admin_add_admin_handler, pattern="^admin_add_admin"))
        application.add_handler(CallbackQueryHandler(admin_remove_admin_handler, pattern="^admin_remove_admin"))
        application.add_handler(CallbackQueryHandler(admin_activity_handler, pattern="^admin_activity"))
        application.add_handler(CallbackQueryHandler(admin_activity_by_chats_handler, pattern="^admin_activity_by_chats"))
        application.add_handler(CallbackQueryHandler(admin_chat_activity_handler, pattern="^admin_chat_activity_"))
        application.add_handler(CallbackQueryHandler(admin_refresh_handler, pattern="^admin_refresh"))
        application.add_handler(CallbackQueryHandler(admin_broadcast_handler, pattern="^admin_broadcast"))
        application.add_handler(CallbackQueryHandler(admin_check_subscriptions_handler, pattern="^admin_check_subscriptions"))
        application.add_handler(CallbackQueryHandler(admin_send_to_group_handler, pattern="^admin_send_to_group"))
        
        # Обработчики активности в группе (должны быть ПЕРВЫМИ!)
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, group_member_handler_func))
        application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, group_left_member_handler_func))
        
        # Сообщения из группы (для отслеживания активности)
        from config.settings import get_settings
        settings = get_settings()
        if settings.GROUP_ID:
            # Обработчик ВСЕХ типов сообщений ТОЛЬКО для нашей группы
            group_filter = filters.Chat(chat_id=int(settings.GROUP_ID)) & ~filters.COMMAND
            application.add_handler(MessageHandler(group_filter, group_message_handler_func))
        
        # Личные сообщения пользователей (работают всегда)
        # ВАЖНО: Порядок имеет значение! Сначала обрабатываем админские команды, потом общие
        
        # Админские обработчики ввода ID (только для личных сообщений)
        from config.settings import get_settings
        settings = get_settings()
        
        # Фильтр для личных сообщений (не групповых)
        private_filter = filters.TEXT & ~filters.COMMAND & ~filters.Chat(chat_id=int(settings.GROUP_ID)) if settings.GROUP_ID else filters.TEXT & ~filters.COMMAND
        
        application.add_handler(MessageHandler(private_filter, handle_admin_id_input))
        application.add_handler(MessageHandler(private_filter, handle_user_id_input))
        application.add_handler(MessageHandler(private_filter, handle_group_message_input))
        application.add_handler(MessageHandler(private_filter, start_handler))
        
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
