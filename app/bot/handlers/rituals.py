"""
Обработчик ритуалов для ClubBot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime

from ...services.user_service import UserService
from ...services.ritual_service import RitualService
from ...services.activity_service import ActivityService, ActivityType
from ...models.ritual import RitualType
from ..keyboards.rituals import (
    get_ritual_keyboard, get_ritual_response_keyboard, 
    get_rituals_list_keyboard, get_ritual_stats_keyboard
)


async def ritual_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ритуалов."""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "rituals_list":
            await show_rituals_list(update, context)
        elif query.data == "ritual_morning":
            await show_morning_rituals(update, context)
        elif query.data == "ritual_evening":
            await show_evening_rituals(update, context)
        elif query.data == "ritual_stats":
            await show_ritual_stats(update, context)
        elif query.data.startswith("ritual_start_"):
            await start_ritual(update, context)
        elif query.data.startswith("ritual_complete_"):
            await complete_ritual(update, context)
        elif query.data.startswith("ritual_skip_"):
            await skip_ritual(update, context)
        elif query.data.startswith("ritual_cancel_"):
            await cancel_ritual(update, context)
        elif query.data.startswith("ritual_stats_"):
            await show_ritual_stats_detail(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка в ritual_handler: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_rituals_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список ритуалов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем статистику ритуалов пользователя
        stats = await ritual_service.get_user_ritual_stats(str(db_user.id), 30)
        
        rituals_text = f"""
🧘 <b>Ритуалы ЯДРА</b>

<b>Твоя активность за 30 дней:</b>
• Выполнено ритуалов: {stats.get('completed_rituals', 0)}
• Пропущено ритуалов: {stats.get('skipped_rituals', 0)}
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%

<b>Доступные ритуалы:</b>
• 🌅 Утренние ритуалы - для настройки на день
• 🌙 Вечерние ритуалы - для подведения итогов

<b>Почему ритуалы важны:</b>
• Помогают сохранить дисциплину
• Настраивают на продуктивный день
• Дают время для рефлексии
• Поддерживают ритм развития

Выбери тип ритуалов:
"""
        
        keyboard = get_rituals_list_keyboard()
        
        await update.callback_query.edit_message_text(
            rituals_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_rituals_list: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_morning_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать утренние ритуалы."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем утренние ритуалы
        rituals = await ritual_service.get_rituals_by_type(RitualType.MORNING)
        
        if not rituals:
            morning_text = """
🌅 <b>Утренние ритуалы</b>

<b>Утренние ритуалы не найдены</b>

Обратись к администратору для настройки утренних ритуалов.
"""
        else:
            ritual = rituals[0]  # Берем первый доступный ритуал
            
            morning_text = f"""
🌅 <b>Утренний ритуал</b>

<b>{ritual.title}</b>

{ritual.content}

<b>Время выполнения:</b> {ritual.estimated_duration} минут
<b>Тип:</b> {ritual.ritual_type_display}

<b>Почему утренние ритуалы важны:</b>
• Настраивают на продуктивный день
• Помогают сфокусироваться на целях
• Дают энергию и мотивацию
• Создают позитивный настрой

<b>Готов начать утренний ритуал?</b>
"""
        
        keyboard = get_ritual_keyboard(str(ritual.id)) if rituals else [
            [InlineKeyboardButton("🔙 Назад", callback_data="rituals_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            morning_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_morning_rituals: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_evening_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать вечерние ритуалы."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем вечерние ритуалы
        rituals = await ritual_service.get_rituals_by_type(RitualType.EVENING)
        
        if not rituals:
            evening_text = """
🌙 <b>Вечерние ритуалы</b>

<b>Вечерние ритуалы не найдены</b>

Обратись к администратору для настройки вечерних ритуалов.
"""
        else:
            ritual = rituals[0]  # Берем первый доступный ритуал
            
            evening_text = f"""
🌙 <b>Вечерний ритуал</b>

<b>{ritual.title}</b>

{ritual.content}

<b>Время выполнения:</b> {ritual.estimated_duration} минут
<b>Тип:</b> {ritual.ritual_type_display}

<b>Почему вечерние ритуалы важны:</b>
• Помогают подвести итоги дня
• Дают время для рефлексии
• Настраивают на спокойный сон
• Подготавливают к следующему дню

<b>Готов начать вечерний ритуал?</b>
"""
        
        keyboard = get_ritual_keyboard(str(ritual.id)) if rituals else [
            [InlineKeyboardButton("🔙 Назад", callback_data="rituals_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            evening_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_evening_rituals: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def start_ritual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать ритуал."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID ритуала
        ritual_id = update.callback_query.data.replace("ritual_start_", "")
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем ритуал
        ritual = await ritual_service.get_ritual_by_id(ritual_id)
        if not ritual:
            await update.callback_query.answer("❌ Ритуал не найден")
            return
        
        # Сохраняем ID ритуала в контексте
        context.user_data['current_ritual_id'] = ritual_id
        context.user_data['ritual_start_time'] = datetime.now()
        
        # Показываем инструкции по выполнению ритуала
        start_text = f"""
🧘 <b>Начинаем ритуал</b>

<b>{ritual.title}</b>

<b>Инструкции:</b>
{ritual.instructions}

<b>Время выполнения:</b> {ritual.estimated_duration} минут

<b>Советы:</b>
• Найди тихое место
• Отключи уведомления
• Сосредоточься на процессе
• Не торопись

<b>Когда закончишь, нажми кнопку "Завершить ритуал"</b>
"""
        
        keyboard = get_ritual_response_keyboard(ritual_id)
        
        await update.callback_query.edit_message_text(
            start_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Записываем активность
        await activity_service.create_activity(
            user_id=str(db_user.id),
            activity_type=ActivityType.RITUAL_STARTED,
            description=f"Ритуал '{ritual.title}' начат"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в start_ritual: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def complete_ritual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Завершить ритуал."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID ритуала из контекста
        ritual_id = context.user_data.get('current_ritual_id')
        if not ritual_id:
            await update.callback_query.answer("❌ Ритуал не найден")
            return
        
        # Получаем время начала ритуала
        start_time = context.user_data.get('ritual_start_time')
        if not start_time:
            await update.callback_query.answer("❌ Время начала ритуала не найдено")
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем ритуал
        ritual = await ritual_service.get_ritual_by_id(ritual_id)
        if not ritual:
            await update.callback_query.answer("❌ Ритуал не найден")
            return
        
        # Вычисляем время выполнения
        completion_time = datetime.now()
        duration = (completion_time - start_time).total_seconds() / 60  # в минутах
        
        # Создаем ответ на ритуал
        await ritual_service.create_ritual_response(
            user_id=str(db_user.id),
            ritual_id=ritual_id,
            response_type="completed",
            content=f"Ритуал выполнен за {duration:.1f} минут",
            completion_time=duration
        )
        
        # Показываем сообщение о завершении
        complete_text = f"""
✅ <b>Ритуал завершен!</b>

<b>{ritual.title}</b>

<b>Время выполнения:</b> {duration:.1f} минут
<b>Рекомендуемое время:</b> {ritual.estimated_duration} минут

<b>Отлично!</b> Ты выполнил ритуал и стал на шаг ближе к своей цели.

<b>Что дальше:</b>
• Продолжай выполнять ритуалы каждый день
• Отмечай свой прогресс
• Не сдавайся, даже если пропускаешь

<b>Помни:</b> каждый ритуал - это инвестиция в себя! 💪
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="ritual_stats")],
            [InlineKeyboardButton("🧘 Еще ритуал", callback_data="rituals_list")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            complete_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Записываем активность
        await activity_service.create_activity(
            user_id=str(db_user.id),
            activity_type=ActivityType.RITUAL_COMPLETED,
            description=f"Ритуал '{ritual.title}' завершен за {duration:.1f} минут"
        )
        
        # Очищаем данные из контекста
        context.user_data.pop('current_ritual_id', None)
        context.user_data.pop('ritual_start_time', None)
        
    except Exception as e:
        logger.error(f"Ошибка в complete_ritual: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def skip_ritual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пропустить ритуал."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID ритуала
        ritual_id = update.callback_query.data.replace("ritual_skip_", "")
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем ритуал
        ritual = await ritual_service.get_ritual_by_id(ritual_id)
        if not ritual:
            await update.callback_query.answer("❌ Ритуал не найден")
            return
        
        # Создаем ответ на ритуал (пропущен)
        await ritual_service.create_ritual_response(
            user_id=str(db_user.id),
            ritual_id=ritual_id,
            response_type="skipped",
            content="Ритуал пропущен"
        )
        
        # Показываем сообщение о пропуске
        skip_text = f"""
⏭️ <b>Ритуал пропущен</b>

<b>{ritual.title}</b>

Понимаем, что иногда бывает сложно найти время для ритуалов.

<b>Помни:</b> ритуалы помогают:
• Сохранить дисциплину
• Настроиться на продуктивный день
• Подвести итоги
• Остаться в ритме

<b>Ты можешь выполнить ритуал в любое время</b>

Что хочешь сделать дальше?
"""
        
        keyboard = [
            [InlineKeyboardButton("🧘 Выполнить ритуал", callback_data="rituals_list")],
            [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="ritual_stats")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            skip_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Записываем активность
        await activity_service.create_activity(
            user_id=str(db_user.id),
            activity_type=ActivityType.RITUAL_SKIPPED,
            description=f"Ритуал '{ritual.title}' пропущен"
        )
        
        # Очищаем данные из контекста
        context.user_data.pop('current_ritual_id', None)
        context.user_data.pop('ritual_start_time', None)
        
    except Exception as e:
        logger.error(f"Ошибка в skip_ritual: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def cancel_ritual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отменить ритуал."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID ритуала
        ritual_id = update.callback_query.data.replace("ritual_cancel_", "")
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем ритуал
        ritual = await ritual_service.get_ritual_by_id(ritual_id)
        if not ritual:
            await update.callback_query.answer("❌ Ритуал не найден")
            return
        
        # Показываем сообщение об отмене
        cancel_text = f"""
❌ <b>Ритуал отменен</b>

<b>{ritual.title}</b>

Ритуал отменен. Ты можешь начать его в любое время.

<b>Помни:</b> ритуалы - это не обязательство, а инструмент для развития.

Что хочешь сделать дальше?
"""
        
        keyboard = [
            [InlineKeyboardButton("🧘 Начать ритуал", callback_data=f"ritual_start_{ritual_id}")],
            [InlineKeyboardButton("📊 Статистика ритуалов", callback_data="ritual_stats")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            cancel_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Записываем активность
        await activity_service.create_activity(
            user_id=str(db_user.id),
            activity_type=ActivityType.RITUAL_CANCELLED,
            description=f"Ритуал '{ritual.title}' отменен"
        )
        
        # Очищаем данные из контекста
        context.user_data.pop('current_ritual_id', None)
        context.user_data.pop('ritual_start_time', None)
        
    except Exception as e:
        logger.error(f"Ошибка в cancel_ritual: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_ritual_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику ритуалов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем статистику ритуалов
        stats = await ritual_service.get_user_ritual_stats(str(db_user.id), 30)
        
        stats_text = f"""
📊 <b>Статистика ритуалов</b>

<b>За последние 30 дней:</b>

🧘 <b>Общая статистика:</b>
• Выполнено ритуалов: {stats.get('completed_rituals', 0)}
• Пропущено ритуалов: {stats.get('skipped_rituals', 0)}
• Всего ритуалов: {stats.get('total_rituals', 0)}

📈 <b>Активность:</b>
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%
• Среднее время выполнения: {stats.get('avg_completion_time', 0):.1f} минут

<b>Анализ:</b>
"""
        
        # Добавляем анализ
        if stats.get('completion_rate', 0) > 80:
            stats_text += "• Отличная активность! Ты на правильном пути 🎉\n"
        elif stats.get('completion_rate', 0) > 50:
            stats_text += "• Хорошая активность! Продолжай в том же духе 👍\n"
        else:
            stats_text += "• Нужно больше активности! Попробуй выполнять ритуалы чаще 📈\n"
        
        if stats.get('avg_completion_time', 0) > 0:
            stats_text += "• Ты тратишь время на ритуалы - это хорошо! ⏰\n"
        else:
            stats_text += "• Попробуй выполнять ритуалы более внимательно 🧘\n"
        
        keyboard = get_ritual_stats_keyboard()
        
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_ritual_stats: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_ritual_stats_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать детальную статистику ритуалов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем тип статистики
        stats_type = update.callback_query.data.replace("ritual_stats_", "")
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        ritual_service = RitualService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        if stats_type == "general":
            # Общая статистика
            stats = await ritual_service.get_user_ritual_stats(str(db_user.id), 30)
            
            stats_text = f"""
📊 <b>Общая статистика ритуалов</b>

<b>За последние 30 дней:</b>
• Выполнено: {stats.get('completed_rituals', 0)}
• Пропущено: {stats.get('skipped_rituals', 0)}
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%
• Среднее время: {stats.get('avg_completion_time', 0):.1f} мин

<b>Рекомендации:</b>
"""
            
            if stats.get('completion_rate', 0) > 80:
                stats_text += "• Отличная работа! Продолжай в том же духе 🎉\n"
            elif stats.get('completion_rate', 0) > 50:
                stats_text += "• Хорошая активность! Попробуй увеличить частоту 👍\n"
            else:
                stats_text += "• Нужно больше дисциплины! Начни с малого 📈\n"
        
        elif stats_type == "morning":
            # Статистика утренних ритуалов
            stats = await ritual_service.get_user_ritual_stats_by_type(str(db_user.id), RitualType.MORNING, 30)
            
            stats_text = f"""
🌅 <b>Статистика утренних ритуалов</b>

<b>За последние 30 дней:</b>
• Выполнено: {stats.get('completed_rituals', 0)}
• Пропущено: {stats.get('skipped_rituals', 0)}
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%

<b>Польза утренних ритуалов:</b>
• Настраивают на продуктивный день
• Дают энергию и мотивацию
• Помогают сфокусироваться на целях
"""
        
        elif stats_type == "evening":
            # Статистика вечерних ритуалов
            stats = await ritual_service.get_user_ritual_stats_by_type(str(db_user.id), RitualType.EVENING, 30)
            
            stats_text = f"""
🌙 <b>Статистика вечерних ритуалов</b>

<b>За последние 30 дней:</b>
• Выполнено: {stats.get('completed_rituals', 0)}
• Пропущено: {stats.get('skipped_rituals', 0)}
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%

<b>Польза вечерних ритуалов:</b>
• Помогают подвести итоги дня
• Дают время для рефлексии
• Настраивают на спокойный сон
"""
        
        elif stats_type == "progress":
            # Статистика прогресса
            stats = await ritual_service.get_user_ritual_progress(str(db_user.id), 30)
            
            stats_text = f"""
📈 <b>Прогресс ритуалов</b>

<b>За последние 30 дней:</b>
• Дней с ритуалами: {stats.get('days_with_rituals', 0)}
• Самая длинная серия: {stats.get('longest_streak', 0)} дней
• Текущая серия: {stats.get('current_streak', 0)} дней

<b>Тренд:</b>
"""
            
            if stats.get('current_streak', 0) > 7:
                stats_text += "• Отличная серия! Не прерывай её 🔥\n"
            elif stats.get('current_streak', 0) > 3:
                stats_text += "• Хорошая серия! Продолжай 💪\n"
            else:
                stats_text += "• Начни новую серию! Каждый день важен 📅\n"
        
        else:
            stats_text = "❌ Неизвестный тип статистики"
        
        keyboard = [
            [InlineKeyboardButton("🔙 К статистике ритуалов", callback_data="ritual_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_ritual_stats_detail: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


# Экспорт основного обработчика (уже определен в начале файла)
