"""
Обработчик для получения информации о группах и каналах.
"""

from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from app.core.database import get_db_session
from app.services.user_service import UserService


async def handle_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик для получения информации о текущем чате.
    
    Показывает ID чата, тип, название - полезно для настройки бота.
    """
    try:
        chat = update.effective_chat
        user = update.effective_user
        
        if not user:
            return
            
        # Проверяем что пользователь админ
        async with get_db_session() as session:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(user.id)
            
            if not db_user or user.id not in [1670311707]:  # ID супер-админа
                await update.message.reply_text("❌ Команда доступна только администраторам")
                return
        
        # Формируем информацию о чате
        info_lines = [
            "📊 **Информация о чате:**",
            "",
            f"🆔 **ID чата:** `{chat.id}`",
            f"📝 **Название:** {chat.title or 'Не указано'}",
            f"📊 **Тип:** {chat.type}",
        ]
        
        if chat.username:
            info_lines.append(f"🔗 **Username:** @{chat.username}")
            
        if chat.description:
            info_lines.append(f"📄 **Описание:** {chat.description}")
            
        # Добавляем специальную информацию для групп
        if chat.type in ['group', 'supergroup']:
            info_lines.extend([
                "",
                "⚙️ **Для настройки бота:**",
                f"```",
                f"GROUP_ID={chat.id}",
                f"```",
                "",
                "💡 Скопируйте ID и добавьте в .env файл"
            ])
            
        message = "\n".join(info_lines)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown"
        )
        
        logger.info(f"Отправлена информация о чате {chat.id} пользователю {user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка в handle_group_info: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении информации о чате"
        )


# Экспортируем обработчик
group_info_handler = handle_group_info
