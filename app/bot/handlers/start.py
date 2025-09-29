"""
Обработчик команды /start.

Обрабатывает команду /start и создает нового пользователя.
"""

from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from loguru import logger

from app.core.database import get_db_session
from app.services import UserService, TelegramService
from app.schemas.user import UserCreate


async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        # Получаем данные пользователя
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        if not user:
            logger.error("Не удалось получить данные пользователя")
            return
        
        # Получаем сессию базы данных
        async with get_db_session() as session:
            user_service = UserService(session)
            telegram_service = TelegramService(context.bot)
            
            # Сначала проверяем подписку на группу "ЯДРО КЛУБА / ОСНОВА PUTИ" согласно ТЗ
            is_subscribed = await telegram_service.check_user_subscription(user.id)
            
            if not is_subscribed:
                # Если не подписан - создаем пригласительную ссылку и отправляем сообщение
                try:
                    # Создаем пригласительную ссылку (действует 24 часа)
                    from datetime import datetime, timedelta
                    expire_date = datetime.now() + timedelta(hours=24)
                    invite_link = await telegram_service.create_group_invite_link(expire_date=expire_date)
                    
                    if invite_link:
                        subscription_message = f"""❌ Для доступа к боту необходимо подписаться на группу "ЯДРО КЛУБА / ОСНОВА PUTИ"

🔗 Ссылка для вступления:
{invite_link}

После подписки нажмите /start еще раз."""
                    else:
                        subscription_message = """❌ Для доступа к боту необходимо подписаться на группу "ЯДРО КЛУБА / ОСНОВА PUTИ"

После подписки нажмите /start еще раз."""
                        
                except Exception as e:
                    logger.error(f"Ошибка создания пригласительной ссылки: {e}")
                    subscription_message = """❌ Для доступа к боту необходимо подписаться на группу "ЯДРО КЛУБА / ОСНОВА PUTИ"

После подписки нажмите /start еще раз."""
                
                await update.message.reply_text(subscription_message)
                return
            
            # Проверяем, существует ли пользователь
            existing_user = await user_service.get_user_by_telegram_id(user.id)
            
            if existing_user:
                logger.info(f"Пользователь {user.id} уже существует и подписан на группу")
                
                # Обновляем статус подписки на группу
                from app.schemas.user import UserUpdate
                await user_service.update_user(str(existing_user.id), UserUpdate(
                    is_subscribed_to_channel=True
                ))
                
                # Проверяем, есть ли активная подписка (оплата)
                if existing_user.subscription_until and existing_user.subscription_until > datetime.now():
                    # У пользователя есть активная подписка - отправляем сообщение о доступе
                    await telegram_service.send_subscription_active_message(
                        user_id=user.id,
                        username=user.first_name or user.username or str(user.id),
                        subscription_until=existing_user.subscription_until,
                        reply_to_message=update.message  # Передаем сообщение для reply
                    )
                else:
                    # У пользователя нет активной подписки - отправляем сообщение о необходимости оплаты
                    await telegram_service.send_payment_required_message(
                        user_id=user.id,
                        reply_to_message=update.message  # Передаем сообщение для reply
                    )
            else:
                # Создаем нового пользователя
                user_data = UserCreate(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                
                new_user = await user_service.create_user(user_data)
                logger.info(f"Создан новый пользователь: {new_user.id} (подписан на @osnovaputi)")
                
                # Отправляем сообщение о необходимости оплаты
                await telegram_service.send_payment_required_message(
                    user_id=user.id,
                    reply_to_message=update.message  # Передаем сообщение для reply
                )
        
    except Exception as e:
        logger.error(f"Ошибка обработки команды /start: {e}")
        
        # Отправляем сообщение об ошибке пользователю
        try:
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке команды. Попробуйте позже или обратитесь к администратору."
            )
        except Exception as reply_error:
            logger.error(f"Ошибка отправки сообщения об ошибке: {reply_error}")


# Экспортируем функцию-обработчик
start_handler = start_command_handler
