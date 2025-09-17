"""
Упрощенные административные обработчики для ClubBot.

Базовая функциональность для администраторов без сложных сервисов.
"""

from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session
from app.services import UserService, PaymentService, RitualService
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from config.settings import settings


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Основной обработчик административных команд.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        # Проверяем права администратора
        user_id = update.effective_user.id
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора")
            return
        
        callback_data = query.data
        
        if callback_data == "admin_panel":
            await show_admin_panel(update, context)
        elif callback_data == "admin_stats":
            await show_stats(update, context)
        elif callback_data == "admin_users":
            await show_users(update, context)
        elif callback_data == "admin_payments":
            await show_payments(update, context)
        elif callback_data == "admin_rituals":
            await show_rituals(update, context)
        else:
            await query.edit_message_text("❌ Неизвестная команда администратора")
            
    except Exception as e:
        logger.error(f"Ошибка в admin_handler: {e}")
        if update.callback_query:
            await update.callback_query.answer("❌ Произошла ошибка")


async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать главную панель администратора."""
    try:
        admin_text = """
🔧 <b>Панель администратора</b>

<b>Добро пожаловать в админ-панель ClubBot!</b>

Доступные функции:
• 📊 Статистика - общая статистика бота
• 👥 Пользователи - управление пользователями
• 💳 Платежи - информация о платежах
• 🧘 Ритуалы - управление ритуалами

<b>Выберите действие:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("💳 Платежи", callback_data="admin_payments")],
            [InlineKeyboardButton("🧘 Ритуалы", callback_data="admin_rituals")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            admin_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_admin_panel: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику бота."""
    try:
        async with get_db_session() as session:
            user_service = UserService(session)
            payment_service = PaymentService(session)
            
            # Получаем статистику пользователей
            user_stats = await user_service.get_user_statistics()
            
            # Получаем статистику платежей
            total_payments = await payment_service.get_payments_count()
            total_revenue = await payment_service.get_total_revenue()
            
            stats_text = f"""
📊 <b>Статистика ClubBot</b>

<b>👥 Пользователи:</b>
• Всего: {user_stats.get('total', 0)}
• Активных: {user_stats.get('active', 0)}
• Неактивных: {user_stats.get('inactive', 0)}
• Заблокированных: {user_stats.get('banned', 0)}

<b>📈 Рост:</b>
• Новых сегодня: {user_stats.get('new_today', 0)}
• Новых за неделю: {user_stats.get('new_week', 0)}
• Новых за месяц: {user_stats.get('new_month', 0)}

<b>💳 Платежи:</b>
• Всего платежей: {total_payments}
• Общий доход: {total_revenue:.2f} ₽

<b>📊 Активность:</b>
• Процент активности: {user_stats.get('activity_rate', 0)}%

<b>Обновлено:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_stats: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать информацию о пользователях."""
    try:
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Получаем последних пользователей
            recent_users = await user_service.get_recent_users(limit=5)
            
            users_text = """
👥 <b>Управление пользователями</b>

<b>Последние пользователи:</b>
"""
            
            for user in recent_users:
                status_emoji = {
                    'active': '✅',
                    'inactive': '⏸️',
                    'banned': '🚫',
                    'pending': '⏳'
                }.get(user.status, '❓')
                
                users_text += f"\n{status_emoji} {user.display_name}"
                users_text += f"\n   ID: {user.telegram_id}"
                users_text += f"\n   Статус: {user.status}"
                users_text += f"\n   Создан: {user.created_at.strftime('%d.%m.%Y')}\n"
            
            if not recent_users:
                users_text += "\n• Нет пользователей"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_users")],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                users_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_users: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать информацию о платежах."""
    try:
        async with get_db_session() as session:
            payment_service = PaymentService(session)
            
            # Получаем последние платежи
            recent_payments = await payment_service.get_recent_payments(limit=5)
            
            payments_text = """
💳 <b>Управление платежами</b>

<b>Последние платежи:</b>
"""
            
            for payment in recent_payments:
                status_emoji = {
                    'paid': '✅',
                    'pending': '⏳',
                    'failed': '❌',
                    'cancelled': '🚫',
                    'expired': '⏰'
                }.get(payment.status, '❓')
                
                payments_text += f"\n{status_emoji} {payment.amount} {payment.currency}"
                payments_text += f"\n   Статус: {payment.status}"
                payments_text += f"\n   Создан: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            
            if not recent_payments:
                payments_text += "\n• Нет платежей"
            
            payments_text += f"""

<b>ℹ️ Информация:</b>
Функция платежей временно отключена.
Для активации обратитесь к разработчику.
"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_payments")],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                payments_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_payments: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать информацию о ритуалах."""
    try:
        async with get_db_session() as session:
            ritual_service = RitualService(session)
            
            # Получаем активные ритуалы
            active_rituals = await ritual_service.get_active_rituals()
            
            rituals_text = """
🧘 <b>Управление ритуалами</b>

<b>Активные ритуалы:</b>
"""
            
            for ritual in active_rituals:
                type_emoji = {
                    'morning': '🌅',
                    'evening': '🌙',
                    'weekly_challenge': '🎯',
                    'weekly_goals': '📋',
                    'friday_cycle': '🏁'
                }.get(ritual.type, '🧘')
                
                rituals_text += f"\n{type_emoji} {ritual.name}"
                rituals_text += f"\n   Тип: {ritual.type}"
                rituals_text += f"\n   Время: {ritual.send_hour:02d}:{ritual.send_minute:02d}"
                rituals_text += f"\n   Активен: {'✅' if ritual.is_active else '❌'}\n"
            
            if not active_rituals:
                rituals_text += "\n• Нет активных ритуалов"
            
            rituals_text += f"""

<b>ℹ️ Информация:</b>
Для создания ритуалов используйте RitualService.
Подробное управление будет добавлено в следующих версиях.
"""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_rituals")],
                [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                rituals_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_rituals: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")

