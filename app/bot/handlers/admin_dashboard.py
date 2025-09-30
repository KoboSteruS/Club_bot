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


async def safe_answer_callback(query, text: str = None) -> bool:
    """
    Безопасный ответ на callback query с обработкой устаревших запросов.
    
    Args:
        query: Callback query объект
        text: Текст для ответа (опционально)
        
    Returns:
        bool: True если ответ отправлен успешно
    """
    try:
        await query.answer(text=text)
        return True
    except Exception as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            logger.warning(f"Устаревший callback query: {e}")
            return False
        else:
            logger.error(f"Ошибка ответа на callback query: {e}")
            return False


async def admin_dashboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin - админ-панель."""
    try:
        settings = get_settings()
        user_id = update.effective_user.id
        
        # Проверяем, является ли пользователь админом
        if user_id not in settings.admin_ids_list:
            # Проверяем, есть ли message (команда) или это callback query
            if update.message:
                await update.message.reply_text("❌ У вас нет прав администратора.")
            elif update.callback_query:
                await update.callback_query.answer("❌ У вас нет прав администратора.")
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
                [InlineKeyboardButton("🔑 Выдача доступа", callback_data="admin_access")],
                [InlineKeyboardButton("👑 Управление админами", callback_data="admin_management")],
                [InlineKeyboardButton("🚫 Проверить подписки", callback_data="admin_check_subscriptions")],
                [InlineKeyboardButton("📈 Активность", callback_data="admin_activity")],
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_refresh")],
                [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")]
            ])
            
            # Отправляем сообщение в зависимости от типа update
            if update.message:
                await update.message.reply_text(message, reply_markup=keyboard, parse_mode='HTML')
            elif update.callback_query:
                await update.callback_query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_dashboard_handler: {e}")
        # Отправляем ошибку в зависимости от типа update
        if update.message:
            await update.message.reply_text("❌ Произошла ошибка при загрузке админ-панели.")
        elif update.callback_query:
            await update.callback_query.edit_message_text("❌ Произошла ошибка при загрузке админ-панели.")


async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Пользователи' в админ-панели."""
    try:
        query = update.callback_query
        await safe_answer_callback(query)
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Определяем номер страницы из callback_data
            page = 0
            if query.data and query.data.startswith("admin_users_page_"):
                try:
                    page = int(query.data.split("_")[-1])
                except (ValueError, IndexError):
                    page = 0
            elif query.data == "admin_users_current":
                # Если нажата кнопка текущей страницы, ничего не делаем
                return
            
            # Получаем общую статистику
            total_users = await user_service.get_total_users_count()
            active_users = await user_service.get_active_users_count()
            premium_users = await user_service.get_premium_users_count()
            
            # Получаем список всех пользователей с пагинацией
            users_per_page = 10
            recent_users = await user_service.get_recent_users(limit=users_per_page, offset=page * users_per_page)
            
            message = f"""👥 <b>Управление пользователями</b>

📊 <b>Статистика:</b>
• Всего: {total_users}
• Активных: {active_users}
• Premium: {premium_users}

📋 <b>Список пользователей (стр. {page + 1}):</b>
"""
            
            for i, user in enumerate(recent_users, 1):
                status_emoji = "✅" if user.status == "active" else "⏳"
                premium_emoji = "💎" if user.is_premium else "🔓"
                channel_emoji = "📢" if user.is_subscribed_to_channel else "❌"
                
                message += f"{i}. {status_emoji} {premium_emoji} {channel_emoji} <b>{user.first_name}</b>"
                if user.username:
                    message += f" (@{user.username})"
                message += f"\n   ID: {user.telegram_id}\n"
                message += f"   Статус: {user.status}\n"
                if user.subscription_until:
                    message += f"   Подписка до: {user.subscription_until.strftime('%d.%m.%Y')}\n"
                message += f"   Добавлен: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            
            # Создаем клавиатуру с пагинацией
            keyboard_buttons = []
            
            # Кнопки пагинации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"admin_users_page_{page-1}"))
            nav_buttons.append(InlineKeyboardButton(f"{page + 1}", callback_data="admin_users_current"))
            if len(recent_users) == users_per_page:
                nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"admin_users_page_{page+1}"))
            
            if nav_buttons:
                keyboard_buttons.append(nav_buttons)
            
            # Кнопки действий
            keyboard_buttons.extend([
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_users")],
                [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            # Проверяем, изменилось ли сообщение
            try:
                await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            except Exception as edit_error:
                if "Message is not modified" in str(edit_error):
                    # Сообщение не изменилось, просто отвечаем на callback
                    await safe_answer_callback(query, "📋 Данные актуальны")
                else:
                    # Другая ошибка - пересылаем
                    raise edit_error
            
    except Exception as e:
        logger.error(f"Ошибка в admin_users_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке списка пользователей.")


async def admin_access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Выдача доступа' в админ-панели."""
    try:
        query = update.callback_query
        await safe_answer_callback(query)
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Получаем статистику доступа
            total_users = await user_service.get_total_users_count()
            active_users = await user_service.get_active_users_count()
            premium_users = await user_service.get_premium_users_count()
            
            # Получаем пользователей без доступа
            pending_users = await user_service.get_users_by_status("pending")
            
            message = f"""🔑 <b>Управление доступом</b>

📊 <b>Статистика:</b>
• Всего пользователей: {total_users}
• С активным доступом: {active_users}
• Premium пользователей: {premium_users}

👥 <b>Пользователи без доступа ({len(pending_users)}):</b>
"""
            
            for user in pending_users[:5]:  # Показываем первых 5
                channel_emoji = "📢" if user.is_subscribed_to_channel else "❌"
                message += f"\n{channel_emoji} <b>{user.first_name}</b>"
                if user.username:
                    message += f" (@{user.username})"
                message += f"\nID: {user.telegram_id}"
                message += f" | Добавлен: {user.created_at.strftime('%d.%m %H:%M')}"
            
            if len(pending_users) > 5:
                message += f"\n\n... и еще {len(pending_users) - 5} пользователей"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Выдать доступ всем", callback_data="admin_give_access_all")],
                [InlineKeyboardButton("👤 Выдать доступ по ID", callback_data="admin_give_access_by_id")],
                [InlineKeyboardButton("❌ Отменить доступ по ID", callback_data="admin_revoke_access_by_id")],
                [InlineKeyboardButton("🔄 Обновить", callback_data="admin_access")],
                [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_access_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке управления доступом.")


async def admin_give_access_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выдачи доступа всем пользователям."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "⏳ Выдаем доступ всем пользователям...")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Получаем всех пользователей со статусом pending
            pending_users = await user_service.get_users_by_status("pending")
            
            if not pending_users:
                await query.edit_message_text("✅ Нет пользователей для выдачи доступа.")
                return
            
            # Выдаем доступ всем
            updated_count = 0
            from datetime import datetime, timedelta
            from app.schemas.user import UserUpdate
            
            for user in pending_users:
                try:
                    # Устанавливаем статус active и подписку на 30 дней
                    subscription_until = datetime.now() + timedelta(days=30)
                    
                    await user_service.update_user(str(user.id), UserUpdate(
                        status="active",
                        is_premium=True,
                        subscription_until=subscription_until
                    ))
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Ошибка обновления пользователя {user.id}: {e}")
            
            message = f"""✅ <b>Доступ выдан успешно!</b>

👥 Обработано пользователей: {updated_count}
📅 Подписка до: {(datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y')}

Все пользователи теперь имеют доступ к функциям клуба.
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 К управлению доступом", callback_data="admin_access")],
                [InlineKeyboardButton("🔙 К админ-панели", callback_data="admin_dashboard")]
            ])
            
            await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в admin_give_access_all_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при выдаче доступа.")


async def admin_give_access_by_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выдачи доступа по ID пользователя."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "👤 Введите ID пользователя для выдачи доступа")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        # Запрашиваем ID пользователя
        message = """👤 <b>Выдача доступа по ID</b>

Введите Telegram ID пользователя, которому нужно выдать доступ.

<b>Пример:</b> <code>123456789</code>

💡 <b>Как найти ID:</b>
• Попросите пользователя написать боту @userinfobot
• Или используйте команду /start и посмотрите в логах бота

Для отмены нажмите "Назад к панели"."""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
        # Сохраняем состояние для ожидания ввода ID
        context.user_data['waiting_for_user_id'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в admin_give_access_by_id_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при запросе ID пользователя.")


async def handle_user_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода ID пользователя для выдачи доступа."""
    try:
        # Проверяем, ожидаем ли мы ввод ID для выдачи или отмены доступа
        if not (context.user_data.get('waiting_for_user_id', False) or 
                context.user_data.get('waiting_for_revoke_user_id', False)):
            return
        
        # Если ожидаем отмену доступа, вызываем соответствующий обработчик
        if context.user_data.get('waiting_for_revoke_user_id', False):
            await handle_revoke_user_id_input(update, context)
            return
            
        user_message = update.message.text.strip()
        
        # Проверяем, что это число
        try:
            target_user_id = int(user_message)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID. Введите числовой ID пользователя.\n\n"
                "Пример: <code>123456789</code>",
                parse_mode='HTML'
            )
            return
        
        # Проверяем права администратора
        settings = get_settings()
        admin_id = update.effective_user.id
        
        if admin_id not in settings.admin_ids_list:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            context.user_data['waiting_for_user_id'] = False
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Ищем пользователя по Telegram ID
            target_user = await user_service.get_user_by_telegram_id(target_user_id)
            
            if not target_user:
                await update.message.reply_text(
                    f"❌ Пользователь с ID <code>{target_user_id}</code> не найден в базе данных.\n\n"
                    "Убедитесь, что пользователь хотя бы раз писал боту.",
                    parse_mode='HTML'
                )
                context.user_data['waiting_for_user_id'] = False
                return
            
            # Выдаем доступ
            from datetime import datetime, timedelta
            from app.schemas.user import UserUpdate
            
            subscription_until = datetime.now() + timedelta(days=30)
            
            await user_service.update_user(str(target_user.id), UserUpdate(
                status="active",
                is_premium=True,
                subscription_until=subscription_until
            ))
            
            success_message = f"""✅ <b>Доступ выдан успешно!</b>

👤 <b>Пользователь:</b> {target_user.first_name}
🆔 <b>ID:</b> <code>{target_user.telegram_id}</code>
📅 <b>Подписка до:</b> {subscription_until.strftime('%d.%m.%Y %H:%M')}

Пользователь теперь имеет доступ к функциям клуба."""
            
            await update.message.reply_text(success_message, parse_mode='HTML')
            
            # Очищаем состояние
            context.user_data['waiting_for_user_id'] = False
            
    except Exception as e:
        logger.error(f"Ошибка в handle_user_id_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при выдаче доступа.")
        context.user_data['waiting_for_user_id'] = False


async def admin_activity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Активность' в админ-панели."""
    try:
        query = update.callback_query
        await safe_answer_callback(query)
        
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
        await safe_answer_callback(query, "🔄 Обновляем данные...")
        
        # Перенаправляем на главную панель
        await admin_dashboard_handler(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка в admin_refresh_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при обновлении данных.")


async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Рассылка' в админ-панели."""
    try:
        query = update.callback_query
        await safe_answer_callback(query)
        
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


async def admin_revoke_access_by_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик отмены доступа по ID пользователя."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "❌ Введите ID пользователя для отмены доступа")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        # Запрашиваем ID пользователя
        message = """❌ <b>Отмена доступа по ID</b>

Введите Telegram ID пользователя, у которого нужно отменить доступ.

<b>Пример:</b> <code>123456789</code>

💡 <b>Как найти ID:</b>
• Посмотрите в админ-панели в разделе "Пользователи"
• Или используйте команду /start и посмотрите в логах бота

Для отмены нажмите "Назад к панели"."""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_access")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
        # Сохраняем состояние для ожидания ввода ID
        context.user_data['waiting_for_revoke_user_id'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в admin_revoke_access_by_id_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при запросе ID пользователя.")


async def handle_revoke_user_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода ID пользователя для отмены доступа."""
    try:
        # Проверяем, ожидаем ли мы ввод ID для отмены доступа
        if not context.user_data.get('waiting_for_revoke_user_id', False):
            return
            
        user_message = update.message.text.strip()
        
        # Проверяем, что это число
        try:
            target_user_id = int(user_message)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID. Введите числовой ID пользователя.\n\n"
                "Пример: <code>123456789</code>",
                parse_mode='HTML'
            )
            return
        
        # Проверяем права администратора
        settings = get_settings()
        admin_id = update.effective_user.id
        
        if admin_id not in settings.admin_ids_list:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            context.user_data['waiting_for_revoke_user_id'] = False
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Ищем пользователя по Telegram ID
            target_user = await user_service.get_user_by_telegram_id(target_user_id)
            
            if not target_user:
                await update.message.reply_text(
                    f"❌ Пользователь с ID <code>{target_user_id}</code> не найден в базе данных.\n\n"
                    "Убедитесь, что пользователь хотя бы раз писал боту.",
                    parse_mode='HTML'
                )
                context.user_data['waiting_for_revoke_user_id'] = False
                return
            
            # Отменяем доступ
            from app.schemas.user import UserUpdate
            
            await user_service.update_user(str(target_user.id), UserUpdate(
                status="pending",
                is_premium=False,
                subscription_until=None
            ))
            
            success_message = f"""✅ <b>Доступ отменен успешно!</b>

👤 <b>Пользователь:</b> {target_user.first_name}
🆔 <b>ID:</b> <code>{target_user.telegram_id}</code>
📅 <b>Статус:</b> pending (доступ отменен)

Пользователь больше не имеет доступ к функциям клуба."""
            
            await update.message.reply_text(success_message, parse_mode='HTML')
            
            # Очищаем состояние
            context.user_data['waiting_for_revoke_user_id'] = False
            
    except Exception as e:
        logger.error(f"Ошибка в handle_revoke_user_id_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отмене доступа.")
        context.user_data['waiting_for_revoke_user_id'] = False


async def admin_management_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик управления администраторами."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "👑 Управление администраторами")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id not in settings.admin_ids_list:
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        # Проверяем, является ли пользователь супер-администратором
        if user_id != settings.SUPER_ADMIN_ID:
            await query.edit_message_text("❌ Только супер-администратор может управлять администраторами.")
            return
        
        # Получаем список текущих администраторов
        from app.services.admin_service import AdminService
        admin_service = AdminService()
        current_admins = await admin_service.get_current_admins()
        
        # Формируем сообщение
        message = "👑 <b>Управление администраторами</b>\n\n"
        message += "<b>Текущие администраторы:</b>\n"
        
        for admin in current_admins:
            status = "🔴 Супер-админ" if admin['is_super_admin'] else "🟡 Админ"
            message += f"• ID: <code>{admin['id']}</code> - {status}\n"
        
        message += f"\n<b>Супер-администратор:</b> <code>{settings.SUPER_ADMIN_ID}</code>"
        message += "\n\nВыберите действие:"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add_admin")],
            [InlineKeyboardButton("➖ Удалить админа", callback_data="admin_remove_admin")],
            [InlineKeyboardButton("🔙 Назад к панели", callback_data="admin_dashboard")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в admin_management_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке управления администраторами.")


async def admin_add_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик добавления администратора."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "➕ Добавление администратора")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id != settings.SUPER_ADMIN_ID:
            await query.edit_message_text("❌ Только супер-администратор может добавлять администраторов.")
            return
        
        message = """➕ <b>Добавление администратора</b>

Введите Telegram ID пользователя, которого нужно сделать администратором.

<b>Пример:</b> <code>123456789</code>

💡 <b>Как найти ID:</b>
• Попросите пользователя написать боту /start
• Посмотрите в логах бота или в админ-панели

Для отмены нажмите "Назад к управлению"."""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад к управлению", callback_data="admin_management")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
        # Сохраняем состояние для ожидания ввода ID
        context.user_data['waiting_for_add_admin_id'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в admin_add_admin_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при запросе ID администратора.")


async def admin_remove_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик удаления администратора."""
    try:
        query = update.callback_query
        await safe_answer_callback(query, "➖ Удаление администратора")
        
        settings = get_settings()
        user_id = query.from_user.id
        
        if user_id != settings.SUPER_ADMIN_ID:
            await query.edit_message_text("❌ Только супер-администратор может удалять администраторов.")
            return
        
        message = """➖ <b>Удаление администратора</b>

Введите Telegram ID администратора, которого нужно удалить.

<b>Пример:</b> <code>123456789</code>

⚠️ <b>Внимание:</b>
• Супер-администратора удалить нельзя
• Удаленный пользователь потеряет доступ к админ-панели

Для отмены нажмите "Назад к управлению"."""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Назад к управлению", callback_data="admin_management")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode='HTML')
        
        # Сохраняем состояние для ожидания ввода ID
        context.user_data['waiting_for_remove_admin_id'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в admin_remove_admin_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при запросе ID администратора.")


async def handle_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода ID администратора."""
    try:
        # Проверяем, ожидаем ли мы ввод ID для добавления админа
        if context.user_data.get('waiting_for_add_admin_id', False):
            await handle_add_admin_id_input(update, context)
            return
        
        # Проверяем, ожидаем ли мы ввод ID для удаления админа
        if context.user_data.get('waiting_for_remove_admin_id', False):
            await handle_remove_admin_id_input(update, context)
            return
            
    except Exception as e:
        logger.error(f"Ошибка в handle_admin_id_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обработке ID администратора.")


async def handle_add_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода ID для добавления администратора."""
    try:
        user_message = update.message.text.strip()
        
        # Проверяем, что это число
        try:
            admin_id = int(user_message)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID. Введите числовой ID пользователя.\n\n"
                "Пример: <code>123456789</code>",
                parse_mode='HTML'
            )
            return
        
        # Проверяем права администратора
        settings = get_settings()
        current_admin_id = update.effective_user.id
        
        if current_admin_id != settings.SUPER_ADMIN_ID:
            await update.message.reply_text("❌ Только супер-администратор может добавлять администраторов.")
            context.user_data['waiting_for_add_admin_id'] = False
            return
        
        # Добавляем администратора
        from app.services.admin_service import AdminService
        admin_service = AdminService()
        
        result = await admin_service.add_admin(admin_id, current_admin_id)
        
        if result['success']:
            success_message = f"""✅ <b>Администратор добавлен успешно!</b>

👤 <b>ID:</b> <code>{admin_id}</code>
📅 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

{result['message']}

✅ <b>Изменения применены мгновенно!</b>
• Новый администратор получил доступ к админ-панели"""
            
            await update.message.reply_text(success_message, parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ {result['message']}")
        
        # Очищаем состояние
        context.user_data['waiting_for_add_admin_id'] = False
        
    except Exception as e:
        logger.error(f"Ошибка в handle_add_admin_id_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при добавлении администратора.")
        context.user_data['waiting_for_add_admin_id'] = False


async def handle_remove_admin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода ID для удаления администратора."""
    try:
        user_message = update.message.text.strip()
        
        # Проверяем, что это число
        try:
            admin_id = int(user_message)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат ID. Введите числовой ID администратора.\n\n"
                "Пример: <code>123456789</code>",
                parse_mode='HTML'
            )
            return
        
        # Проверяем права администратора
        settings = get_settings()
        current_admin_id = update.effective_user.id
        
        if current_admin_id != settings.SUPER_ADMIN_ID:
            await update.message.reply_text("❌ Только супер-администратор может удалять администраторов.")
            context.user_data['waiting_for_remove_admin_id'] = False
            return
        
        # Удаляем администратора
        from app.services.admin_service import AdminService
        admin_service = AdminService()
        
        result = await admin_service.remove_admin(admin_id, current_admin_id)
        
        if result['success']:
            success_message = f"""✅ <b>Администратор удален успешно!</b>

👤 <b>ID:</b> <code>{admin_id}</code>
📅 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

{result['message']}

✅ <b>Изменения применены мгновенно!</b>
• Пользователь потерял доступ к админ-панели"""
            
            await update.message.reply_text(success_message, parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ {result['message']}")
        
        # Очищаем состояние
        context.user_data['waiting_for_remove_admin_id'] = False
        
    except Exception as e:
        logger.error(f"Ошибка в handle_remove_admin_id_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при удалении администратора.")
        context.user_data['waiting_for_remove_admin_id'] = False


async def admin_check_subscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик проверки подписок участников группы."""
    try:
        query = update.callback_query
        await query.answer("🔍 Проверяем подписки...")
        
        # Показываем сообщение о начале проверки
        await query.edit_message_text(
            "🔍 <b>Проверка подписок участников группы</b>\n\n"
            "⏳ Идет проверка всех участников...\n"
            "📤 Отправка предупреждений неоплатившим...\n"
            "⏰ Планирование исключений через 30 минут...",
            parse_mode='HTML'
        )
        
        # Импортируем сервис управления группой
        from app.services.group_management_service import GroupManagementService
        
        # Получаем бота из контекста
        bot = context.bot
        group_service = GroupManagementService(bot)
        
        # Выполняем проверку
        results = await group_service.check_subscriptions_and_kick_unpaid()
        
        # Формируем отчет
        report_message = f"""✅ <b>Проверка подписок завершена!</b>

📊 <b>Результаты:</b>
• 👥 Проверено участников: {results['total_checked']}
• ⚠️ Отправлено предупреждений: {results['warnings_sent']}
• 🚫 Исключено пользователей: {results['kicked_users']}
• ❌ Ошибок: {results['errors']}

📋 <b>Детали:</b>"""

        # Добавляем детали
        if results['details']:
            for detail in results['details'][:10]:  # Показываем первые 10
                if detail.get('action') == 'warning_sent':
                    report_message += f"\n• ⚠️ Предупреждение: @{detail.get('username', 'unknown')} (ID: {detail['user_id']})"
                elif detail.get('action') == 'error':
                    report_message += f"\n• ❌ Ошибка: {detail['message']}"
        
        if len(results['details']) > 10:
            report_message += f"\n• ... и еще {len(results['details']) - 10} записей"
        
        report_message += f"""

⏰ <b>Следующая проверка:</b> через 30 минут
🔄 <b>Автоматическая проверка:</b> каждые 30 минут

💡 <b>Важно:</b>
• Пользователи получат 30 минут на оплату
• Исключение произойдет автоматически
• Можно добавить обратно через админ-панель"""

        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Проверить еще раз", callback_data="admin_check_subscriptions")],
            [InlineKeyboardButton("🔙 Назад", callback_data="admin_back")]
        ])
        
        await query.edit_message_text(report_message, reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в admin_check_subscriptions_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при проверке подписок.")
