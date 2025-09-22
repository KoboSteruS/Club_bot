"""
Админ-панель для мониторинга активности в канале.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.services.user_service import UserService
from app.services.payment_service import PaymentService
from app.services.activity_service import ActivityService
from app.services.telegram_service import TelegramService
from config.settings import get_settings


async def admin_dashboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin - админ-панель."""
    try:
        settings = get_settings()
        user_id = update.effective_user.id
        
        # Проверяем, является ли пользователь админом
        if user_id not in settings.admin_ids_list:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        # Получаем статистику
        async with get_db_session() as session:
            user_service = UserService(session)
            payment_service = PaymentService(session)
            activity_service = ActivityService(session)
            
            # Общая статистика пользователей
            total_users = await user_service.get_total_users_count()
            active_users = await user_service.get_active_users_count()
            premium_users = await user_service.get_premium_users_count()
            
            # Статистика за последние 24 часа
            yesterday = datetime.utcnow() - timedelta(days=1)
            new_users_today = await user_service.get_new_users_count_since(yesterday)
            
            # Статистика платежей
            total_payments = await payment_service.get_total_payments_count()
            successful_payments = await payment_service.get_successful_payments_count()
            
            # Статистика активности
            active_today = await activity_service.get_active_users_count_since(yesterday)
            
            # Создаем сообщение с статистикой
            message = f"""
📊 <b>Админ-панель ОСНОВА ПУТИ</b>

👥 <b>Пользователи:</b>
• Всего: {total_users}
• Активных: {active_users}
• Premium: {premium_users}
• Новых за 24ч: {new_users_today}

💳 <b>Платежи:</b>
• Всего: {total_payments}
• Успешных: {successful_payments}

⚡ <b>Активность:</b>
• Активных за 24ч: {active_today}

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
            
            # Создаем клавиатуру
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
                [InlineKeyboardButton("💳 Платежи", callback_data="admin_payments")],
                [InlineKeyboardButton("📈 Активность", callback_data="admin_activity")],
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_refresh")],
                [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")]
            ])
            
            await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_dashboard_handler: {e}")
        await update.message.reply_text("❌ Произошла ошибка при загрузке админ-панели.")


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Пользователи' в админ-панели."""
    try:
        query = update.callback_query
        await query.answer()
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Получаем список последних пользователей
            recent_users = await user_service.get_recent_users(limit=10)
            
            message = "👥 <b>Последние пользователи:</b>\n\n"
            
            for user in recent_users:
                status_emoji = "✅" if user.status == "active" else "⏳"
                premium_emoji = "💎" if user.is_premium else "🔓"
                
                message += f"{status_emoji} {premium_emoji} <b>{user.first_name}</b>"
                if user.username:
                    message += f" (@{user.username})"
                message += f"\nID: {user.telegram_id}\n"
                message += f"Статус: {user.status}\n"
                message += f"Добавлен: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_users_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке списка пользователей.")


async def admin_payments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Платежи' в админ-панели."""
    try:
        query = update.callback_query
        await query.answer()
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            payment_service = PaymentService(session)
            
            # Получаем статистику платежей
            total_amount = await payment_service.get_total_payments_amount()
            today_amount = await payment_service.get_today_payments_amount()
            
            # Получаем последние платежи
            recent_payments = await payment_service.get_recent_payments(limit=5)
            
            message = f"""💳 <b>Статистика платежей:</b>

💰 Общая сумма: {total_amount:.2f} USDT
📅 За сегодня: {today_amount:.2f} USDT

<b>Последние платежи:</b>
"""
            
            for payment in recent_payments:
                status_emoji = "✅" if payment.status == "paid" else "⏳"
                message += f"\n{status_emoji} {payment.amount} {payment.currency}"
                message += f" - {payment.status}"
                if payment.paid_at:
                    message += f" ({payment.paid_at.strftime('%d.%m %H:%M')})"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_payments_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке статистики платежей.")


async def admin_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Активность' в админ-панели."""
    try:
        query = update.callback_query
        await query.answer()
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            activity_service = ActivityService(session)
            
            # Получаем статистику активности
            today = datetime.utcnow().date()
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            
            activity_today = await activity_service.get_activity_stats_for_date(today)
            activity_yesterday = await activity_service.get_activity_stats_for_date(yesterday)
            
            message = f"""📈 <b>Активность в канале:</b>

📅 <b>Сегодня ({today.strftime('%d.%m.%Y')}):</b>
• Сообщений: {activity_today.get('messages', 0)}
• Активных пользователей: {activity_today.get('active_users', 0)}

📅 <b>Вчера ({yesterday.strftime('%d.%m.%Y')}):</b>
• Сообщений: {activity_yesterday.get('messages', 0)}
• Активных пользователей: {activity_yesterday.get('active_users', 0)}

⚡ <b>Топ активных пользователей за неделю:</b>
"""
            
            # Получаем топ активных пользователей
            top_users = await activity_service.get_top_active_users(days=7, limit=5)
            
            for i, user in enumerate(top_users, 1):
                message += f"{i}. {user.get('first_name', 'Неизвестно')} - {user.get('activity_count', 0)} сообщений\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_activity_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке статистики активности.")


async def admin_refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Обновить' в админ-панели."""
    try:
        query = update.callback_query
        await query.answer("🔄 Обновляем данные...")
        
        # Перенаправляем на главную панель
        await admin_dashboard_handler(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в admin_refresh_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при обновлении данных.")


async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Рассылка' в админ-панели."""
    try:
        query = update.callback_query
        await query.answer()
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        message = """📢 <b>Рассылка сообщений</b>

Выберите тип рассылки:

• Всем пользователям
• Только активным
• Только premium
• По статусу подписки
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Всем пользователям", callback_data="broadcast_all")],
            [InlineKeyboardButton("✅ Только активным", callback_data="broadcast_active")],
            [InlineKeyboardButton("💎 Только premium", callback_data="broadcast_premium")],
            [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в admin_broadcast_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке меню рассылки.")
