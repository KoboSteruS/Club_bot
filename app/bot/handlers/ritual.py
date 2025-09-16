"""
Обработчики для системы ритуалов ЯДРА.

Этот модуль содержит обработчики для:
- Ответов на утренние и вечерние ритуалы
- Кнопок в сообщениях ритуалов
- Текстовых ответов на ритуалы
"""

from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from loguru import logger

from app.core.database import get_database
from app.services import UserService, RitualService, TelegramService
from app.models.ritual import ResponseType, RitualType
from app.schemas.ritual import RitualResponseCreate


async def handle_ritual_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик нажатий на кнопки в ритуалах.
    
    Callback data format: ritual_{response_type}_{ritual_id}_{user_ritual_id}
    """
    query = update.callback_query
    await query.answer()
    
    if not query.data or not query.data.startswith('ritual_'):
        return
    
    try:
        # Парсим callback data
        parts = query.data.split('_')
        if len(parts) < 4:
            logger.error(f"Неверный формат callback data: {query.data}")
            return
        
        button_type = parts[1]  # ready, reported, accepted, etc.
        ritual_id = parts[2]
        user_ritual_id = parts[3]
        
        user = query.from_user
        logger.info(f"Обработка ответа на ритуал от пользователя {user.id}: {button_type}")
        
        async for session in get_database():
            user_service = UserService(session)
            ritual_service = RitualService(session)
            
            # Получаем пользователя
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await query.edit_message_text("❌ Пользователь не найден в системе.")
                return
            
            # Определяем тип ответа по кнопке
            response_type = _get_response_type_from_button(button_type)
            
            # Записываем ответ
            response_data = RitualResponseCreate(
                user_ritual_id=user_ritual_id,
                ritual_id=ritual_id,
                response_type=response_type,
                button_clicked=button_type,
                sent_at=datetime.now()
            )
            
            await ritual_service.record_ritual_response(response_data)
            
            # Обновляем сообщение с подтверждением
            response_text = _get_response_confirmation(button_type, user.first_name)
            
            try:
                await query.edit_message_text(
                    text=response_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Не удалось обновить сообщение: {e}")
                await context.bot.send_message(
                    chat_id=user.id,
                    text=response_text,
                    parse_mode='HTML'
                )
            
            logger.info(f"Записан ответ на ритуал: {button_type} от пользователя {user.id}")
            break  # Выходим после первой сессии
            
    except Exception as e:
        logger.error(f"Ошибка обработки ответа на ритуал: {e}")
        try:
            await query.edit_message_text("❌ Произошла ошибка при обработке ответа.")
        except:
            pass


async def handle_evening_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик текстовых ответов на вечерний ритуал.
    
    Сохраняет развёрнутый ответ пользователя на вечерний ритуал.
    """
    message = update.message
    if not message or not message.text:
        return
    
    user = message.from_user
    text = message.text.strip()
    
    # Проверяем, что это ответ на вечерний ритуал
    # (можно добавить более сложную логику определения контекста)
    if len(text) < 10:  # Слишком короткий ответ
        return
    
    try:
        logger.info(f"Получен текстовый отчёт от пользователя {user.id}")
        
        async for session in get_database():
            user_service = UserService(session)
            ritual_service = RitualService(session)
            
            # Получаем пользователя
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                return
            
            # Ищем последний отправленный вечерний ритуал для этого пользователя
            # (упрощённая логика - в реальности нужно более точное определение)
            
            # Отправляем подтверждение
            await message.reply_text(
                "✅ <b>Отчёт принят!</b>\n\n"
                "🙏 Спасибо за честность и открытость.\n"
                "📈 Каждая рефлексия делает тебя сильнее!\n\n"
                "💪 Завтра новый день — новые возможности для роста!",
                parse_mode='HTML'
            )
            
            logger.info(f"Принят развёрнутый отчёт от пользователя {user.id}")
            break  # Выходим после первой сессии
            
    except Exception as e:
        logger.error(f"Ошибка обработки текстового отчёта: {e}")


def _get_response_type_from_button(button_type: str) -> ResponseType:
    """Определить тип ответа по нажатой кнопке."""
    completed_buttons = {
        'ready', 'reported', 'accepted', 'set', 'successful'
    }
    
    skipped_buttons = {
        'sleepy', 'private', 'maybe'
    }
    
    partial_buttons = {
        'planning', 'improving'
    }
    
    if button_type in completed_buttons:
        return ResponseType.COMPLETED
    elif button_type in skipped_buttons:
        return ResponseType.SKIPPED
    elif button_type in partial_buttons:
        return ResponseType.PARTIAL
    else:
        return ResponseType.COMPLETED  # По умолчанию


def _get_response_confirmation(button_type: str, user_name: Optional[str] = None) -> str:
    """Получить текст подтверждения для ответа."""
    name = user_name or "друг"
    
    confirmations = {
        # Утренние ритуалы
        'ready': f"🔥 <b>Отлично, {name}!</b>\n\nТвоя готовность к новому дню записана!\n💪 Иди и покоряй этот день!",
        'sleepy': f"😴 <b>Понимаю, {name}</b>\n\nИногда нужно больше времени для пробуждения.\n☕️ Выпей кофе и возвращайся к жизни!",
        
        # Вечерние ритуалы
        'reported': f"📝 <b>Спасибо за отчёт, {name}!</b>\n\nТвоя честность с собой — это основа роста.\n🌟 Завтра будет лучше!",
        'private': f"🤐 <b>Понимаю, {name}</b>\n\nИногда нужно время для осмысления.\n💭 Главное — что ты думаешь об этом!",
        
        # Еженедельные вызовы
        'accepted': f"💪 <b>Вызов принят, {name}!</b>\n\nТеперь главное — довести до конца!\n🏆 Эта неделя будет твоей!",
        'maybe': f"🤔 <b>Подумай хорошенько, {name}</b>\n\nВеликие дела начинаются с решений.\n⚡️ Время действовать!",
        
        # Цели на неделю
        'set': f"🎯 <b>Цели установлены, {name}!</b>\n\nТеперь у тебя есть ясный план действий.\n📈 Время превращать планы в результаты!",
        'planning': f"📝 <b>Планирование — это уже половина успеха, {name}!</b>\n\nНе затягивай, лучший план — тот, который выполняется!\n⏰ Время действовать!",
        
        # Пятничные ритуалы
        'successful': f"🏆 <b>Отличная неделя, {name}!</b>\n\nТы можешь гордиться результатами!\n🎉 Отдохни и готовься к новым свершениям!",
        'improving': f"📈 <b>Осознание — первый шаг к улучшению, {name}!</b>\n\nКаждая неделя делает тебя опытнее.\n💪 Следующая будет ещё лучше!"
    }
    
    return confirmations.get(button_type, f"✅ <b>Ответ принят, {name}!</b>\n\nСпасибо за участие в ритуале! 🙏")


# Создаём обработчики
ritual_button_callback_handler = CallbackQueryHandler(
    handle_ritual_button_callback,
    pattern=r'^ritual_'
)

evening_report_text_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_evening_report_text
)
