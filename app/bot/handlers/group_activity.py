"""
Обработчик активности в группе.

Отслеживает сообщения пользователей в группе "ЯДРО КЛУБА / ОСНОВА PUTИ"
для сбора статистики активности.
"""

from datetime import datetime, date
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from loguru import logger

from app.core.database import get_db_session
from app.services import ActivityService, UserService
from app.models.activity import ActivityType
from config.settings import get_settings


async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик сообщений из группы для отслеживания активности.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        # Проверяем, что сообщение из группы
        if not update.message or not update.message.chat:
            return
            
        chat_id = str(update.message.chat.id)
        settings = get_settings()
        
        # Проверяем, что сообщение из нашей группы
        if chat_id != settings.GROUP_ID:
            return
            
        # Проверяем, что это не бот
        if update.message.from_user.is_bot:
            return
            
        user = update.message.from_user
        message = update.message
        
        logger.info(f"📝 Сообщение в группе от пользователя {user.id} (@{user.username}): {message.text[:50] if message.text else 'медиа'}")
        
        async with get_db_session() as session:
            user_service = UserService(session)
            activity_service = ActivityService(session)
            
            # Получаем или создаем пользователя
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                logger.info(f"Создаем нового пользователя {user.id} из активности в группе")
                from app.schemas.user import UserCreate
                
                user_data = UserCreate(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    status="active",
                    is_in_group=True,
                    joined_group_at=datetime.now()
                )
                db_user = await user_service.create_user(user_data)
            
            # Обновляем статус участия в группе
            if not db_user.is_in_group:
                from app.schemas.user import UserUpdate
                await user_service.update_user(str(db_user.id), UserUpdate(
                    is_in_group=True,
                    joined_group_at=datetime.now()
                ))
                logger.info(f"Пользователь {user.id} отмечен как участник группы")
            
            # Определяем тип активности
            activity_type = ActivityType.MESSAGE
            
            if message.photo:
                activity_type = ActivityType.PHOTO
            elif message.video:
                activity_type = ActivityType.VIDEO
            elif message.document:
                activity_type = ActivityType.DOCUMENT
            elif message.voice:
                activity_type = ActivityType.VOICE
            elif message.sticker:
                activity_type = ActivityType.STICKER
            elif message.poll:
                activity_type = ActivityType.POLL
            elif message.forward_from or message.forward_from_chat:
                activity_type = ActivityType.FORWARD
            elif message.reply_to_message:
                activity_type = ActivityType.REPLY
            
            # Создаем запись активности
            from app.schemas.activity import ChatActivityCreate
            
            activity_data = ChatActivityCreate(
                user_id=str(db_user.id),
                chat_id=chat_id,
                message_id=message.message_id,
                activity_type=activity_type,
                message_text=message.text or message.caption or "",
                message_length=len(message.text or message.caption or ""),
                activity_date=date.today(),
                activity_hour=datetime.now().hour,
                is_reply=bool(message.reply_to_message),
                is_forward=bool(message.forward_from or message.forward_from_chat)
            )
            
            await activity_service.create_chat_activity(activity_data)
            logger.debug(f"Сохранена активность: {activity_type} от пользователя {user.id}")
            
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения из группы: {e}")


async def group_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик новых участников группы.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        if not update.message or not update.message.new_chat_members:
            return
            
        chat_id = str(update.message.chat.id)
        settings = get_settings()
        
        # Проверяем, что это наша группа
        if chat_id != settings.GROUP_ID:
            return
            
        for new_member in update.message.new_chat_members:
            if new_member.is_bot:
                continue
                
            logger.info(f"👋 Новый участник группы: {new_member.id} (@{new_member.username})")
            
            async with get_db_session() as session:
                user_service = UserService(session)
                
                # Получаем или создаем пользователя
                db_user = await user_service.get_user_by_telegram_id(new_member.id)
                if not db_user:
                    from app.schemas.user import UserCreate
                    
                    user_data = UserCreate(
                        telegram_id=new_member.id,
                        username=new_member.username,
                        first_name=new_member.first_name,
                        last_name=new_member.last_name,
                        status="active",
                        is_in_group=True,
                        joined_group_at=datetime.now()
                    )
                    await user_service.create_user(user_data)
                else:
                    # Обновляем статус участия в группе
                    from app.schemas.user import UserUpdate
                    await user_service.update_user(str(db_user.id), UserUpdate(
                        is_in_group=True,
                        joined_group_at=datetime.now()
                    ))
                
                logger.info(f"Пользователь {new_member.id} добавлен в группу")
                
    except Exception as e:
        logger.error(f"Ошибка обработки нового участника группы: {e}")


async def group_left_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик участников, покинувших группу.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        if not update.message or not update.message.left_chat_member:
            return
            
        chat_id = str(update.message.chat.id)
        settings = get_settings()
        
        # Проверяем, что это наша группа
        if chat_id != settings.GROUP_ID:
            return
            
        left_member = update.message.left_chat_member
        if left_member.is_bot:
            return
            
        logger.info(f"👋 Участник покинул группу: {left_member.id} (@{left_member.username})")
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Обновляем статус участия в группе
            db_user = await user_service.get_user_by_telegram_id(left_member.id)
            if db_user:
                from app.schemas.user import UserUpdate
                await user_service.update_user(str(db_user.id), UserUpdate(
                    is_in_group=False
                ))
                logger.info(f"Пользователь {left_member.id} отмечен как покинувший группу")
                
    except Exception as e:
        logger.error(f"Ошибка обработки участника, покинувшего группу: {e}")


# Экспортируем обработчики
group_message_handler_func = group_message_handler
group_member_handler_func = group_member_handler
group_left_member_handler_func = group_left_member_handler
