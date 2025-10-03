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
            logger.debug("Сообщение не из группы или нет chat")
            return
            
        base_chat_id = str(update.message.chat.id)
        settings = get_settings()
        
        logger.debug(f"Получено сообщение из чата {base_chat_id}, ожидаем {settings.GROUP_ID}")
        
        # Проверяем, что сообщение из нашей группы
        if base_chat_id != settings.GROUP_ID:
            logger.debug(f"Сообщение не из нашей группы: {base_chat_id} != {settings.GROUP_ID}")
            return
        
        # Определяем полный ID чата с учетом топика
        chat_id = base_chat_id
        if update.message.message_thread_id:
            # Это сообщение из топика
            chat_id = f"{base_chat_id}_{update.message.message_thread_id}"
            logger.debug(f"Сообщение из топика: {chat_id}")
        else:
            # Это сообщение из основной группы
            logger.debug(f"Сообщение из основной группы: {chat_id}")
            
        # Проверяем, что это не бот
        if update.message.from_user.is_bot:
            logger.debug("Сообщение от бота, пропускаем")
            return
            
        user = update.message.from_user
        message = update.message
        
        # Определяем тип сообщения для логирования
        message_type = "текст"
        if message.video_note:
            message_type = "видеосообщение"
        elif message.voice:
            message_type = "голосовое"
        elif message.video:
            message_type = "видео"
        elif message.audio:
            message_type = "аудио"
        elif message.photo:
            message_type = "фото"
        elif message.animation:
            message_type = "GIF"
        elif message.sticker:
            message_type = "стикер"
        elif message.document:
            message_type = "документ"
        elif message.poll:
            message_type = "опрос"
        elif message.location:
            message_type = "геолокация"
        elif message.contact:
            message_type = "контакт"
        
        logger.info(f"📝 {message_type.title()} в группе от пользователя {user.id} (@{user.username}): {message.text[:50] if message.text else message.caption[:50] if message.caption else ''}")
        
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
            
            # Проверяем пересылку и ответы в первую очередь
            if message.forward_from or message.forward_from_chat:
                activity_type = ActivityType.FORWARD
            elif message.reply_to_message:
                activity_type = ActivityType.REPLY
            # Затем проверяем медиа контент
            elif message.video_note:
                activity_type = ActivityType.VIDEO_NOTE
            elif message.voice:
                activity_type = ActivityType.VOICE
            elif message.video:
                activity_type = ActivityType.VIDEO
            elif message.audio:
                activity_type = ActivityType.AUDIO
            elif message.photo:
                activity_type = ActivityType.PHOTO
            elif message.animation:
                activity_type = ActivityType.ANIMATION
            elif message.sticker:
                activity_type = ActivityType.STICKER
            elif message.document:
                activity_type = ActivityType.DOCUMENT
            elif message.poll:
                activity_type = ActivityType.POLL
            elif message.location:
                activity_type = ActivityType.LOCATION
            elif message.contact:
                activity_type = ActivityType.CONTACT
            elif message.game:
                activity_type = ActivityType.GAME
            elif message.invoice:
                activity_type = ActivityType.INVOICE
            elif message.successful_payment:
                activity_type = ActivityType.SUCCESSFUL_PAYMENT
            
            # Извлекаем информацию о медиа-файлах
            media_file_id = None
            media_duration = None
            media_file_size = None
            
            if message.video_note:
                media_file_id = message.video_note.file_id
                media_duration = message.video_note.duration
                media_file_size = message.video_note.file_size
            elif message.voice:
                media_file_id = message.voice.file_id
                media_duration = message.voice.duration
                media_file_size = message.voice.file_size
            elif message.video:
                media_file_id = message.video.file_id
                media_duration = message.video.duration
                media_file_size = message.video.file_size
            elif message.audio:
                media_file_id = message.audio.file_id
                media_duration = message.audio.duration
                media_file_size = message.audio.file_size
            elif message.photo:
                # Берем самое большое фото
                media_file_id = message.photo[-1].file_id
                media_file_size = message.photo[-1].file_size
            elif message.document:
                media_file_id = message.document.file_id
                media_file_size = message.document.file_size
            elif message.animation:
                media_file_id = message.animation.file_id
                media_file_size = message.animation.file_size
            elif message.sticker:
                media_file_id = message.sticker.file_id
                media_file_size = message.sticker.file_size
            
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
                is_forward=bool(message.forward_from or message.forward_from_chat),
                media_file_id=media_file_id,
                media_duration=media_duration,
                media_file_size=media_file_size
            )
            
            # Записываем активность в изолированной сессии, чтобы не откатывалась при ошибках
            try:
                await ActivityService.record_activity_isolated(activity_data)
                logger.info(f"✅ Сохранена активность: {activity_type} от пользователя {user.id} (@{user.username}) в чате {chat_id}")
            except Exception as activity_error:
                logger.error(f"❌ Ошибка записи активности: {activity_error}")
                # Не прерываем основной поток обработки
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения из группы: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


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
