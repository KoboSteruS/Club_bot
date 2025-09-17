"""
Обработчик целей для ClubBot.

Обрабатывает команды и callback'и связанные с постановкой и управлением целями.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.services.user_service import UserService
from app.services.goal_service import GoalService
from app.services.activity_service import ActivityService, ActivityType
from app.schemas.goal import GoalCreate


async def goal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик callback'ов для целей.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    try:
        query = update.callback_query
        if not query:
            return
            
        await query.answer()
        
        # Разбираем callback data
        callback_data = query.data
        
        if callback_data == "goals_list":
            await show_goals_list(update, context)
        elif callback_data == "goal_create":
            await start_goal_creation(update, context)
        elif callback_data == "goal_weekly":
            await show_weekly_goals(update, context)
        elif callback_data == "goal_stats":
            await show_goals_stats(update, context)
        elif callback_data.startswith("goal_complete_"):
            await complete_goal(update, context)
        elif callback_data.startswith("goal_delete_"):
            await delete_goal(update, context)
        elif callback_data == "set_goal":
            await start_goal_creation(update, context)
        elif callback_data == "skip_goal":
            await skip_goal_setting(update, context)
        else:
            await query.edit_message_text("❌ Неизвестная команда")
            
    except Exception as e:
        logger.error(f"Ошибка в goal_handler: {e}")
        if update.callback_query:
            await update.callback_query.answer("❌ Произошла ошибка")


async def show_goals_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список целей пользователя."""
    try:
        user = update.effective_user
        if not user:
            return
            
        async with get_db_session() as session:
            user_service = UserService(session)
            goal_service = GoalService(session)
            
            # Получаем пользователя из базы
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.callback_query.answer("❌ Пользователь не найден")
                return
            
            # Получаем активные цели пользователя
            active_goals = await goal_service.get_user_active_goals(str(db_user.id))
            completed_goals = await goal_service.get_user_completed_goals(str(db_user.id), limit=5)
            
            goals_text = f"""
🎯 <b>Твои цели</b>

<b>Активные цели ({len(active_goals)}):</b>
"""
            
            if active_goals:
                for i, goal in enumerate(active_goals, 1):
                    deadline_str = ""
                    if goal.deadline:
                        days_left = (goal.deadline.date() - datetime.now().date()).days
                        if days_left > 0:
                            deadline_str = f" (осталось {days_left} дн.)"
                        elif days_left == 0:
                            deadline_str = " (сегодня!)"
                        else:
                            deadline_str = f" (просрочено на {abs(days_left)} дн.)"
                    
                    goals_text += f"• {goal.title}{deadline_str}\n"
            else:
                goals_text += "• Нет активных целей\n"
            
            goals_text += f"\n<b>Выполнено недавно ({len(completed_goals)}):</b>\n"
            
            if completed_goals:
                for goal in completed_goals:
                    completed_date = goal.completed_at.strftime("%d.%m") if goal.completed_at else ""
                    goals_text += f"✅ {goal.title} ({completed_date})\n"
            else:
                goals_text += "• Нет выполненных целей\n"
            
            goals_text += """
<b>Помни:</b> цель без плана — это просто мечта!

Что хочешь сделать?
"""
            
            keyboard = [
                [InlineKeyboardButton("➕ Новая цель", callback_data="goal_create")],
                [InlineKeyboardButton("📊 Статистика", callback_data="goal_stats")],
                [InlineKeyboardButton("📅 Цели на неделю", callback_data="goal_weekly")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                goals_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_goals_list: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def start_goal_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать создание новой цели."""
    try:
        create_text = """
🎯 <b>Создание новой цели</b>

<b>Как создать эффективную цель:</b>
• Сделай её конкретной и измеримой
• Установи реалистичные сроки
• Разбей на небольшие шаги
• Запиши план достижения

<b>Примеры хороших целей:</b>
• "Прочитать 2 книги до конца месяца"
• "Заниматься спортом 3 раза в неделю"
• "Выучить 100 новых слов на английском"

<b>Напиши свою цель в следующем сообщении.</b>

Формат: Название цели (можно добавить срок)
"""
        
        keyboard = [
            [InlineKeyboardButton("❌ Отмена", callback_data="goals_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            create_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Устанавливаем состояние ожидания ввода цели
        context.user_data['waiting_for_goal'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в start_goal_creation: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_weekly_goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать цели на неделю."""
    try:
        user = update.effective_user
        if not user:
            return
            
        async with get_db_session() as session:
            user_service = UserService(session)
            goal_service = GoalService(session)
            
            # Получаем пользователя из базы
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.callback_query.answer("❌ Пользователь не найден")
                return
            
            # Получаем цели на текущую неделю
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_end = week_start + timedelta(days=6)
            
            weekly_goals = await goal_service.get_user_goals_by_period(
                str(db_user.id), week_start, week_end
            )
            
            weekly_text = f"""
📅 <b>Цели на неделю</b>

<b>Неделя {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m')}:</b>

"""
            
            if weekly_goals:
                completed_count = sum(1 for goal in weekly_goals if goal.is_completed)
                weekly_text += f"<b>Прогресс: {completed_count}/{len(weekly_goals)} целей</b>\n\n"
                
                for goal in weekly_goals:
                    status = "✅" if goal.is_completed else "⏳"
                    weekly_text += f"{status} {goal.title}\n"
            else:
                weekly_text += "• Нет целей на эту неделю\n"
            
            weekly_text += """

<b>Рекомендации для недельных целей:</b>
• 3-5 конкретных задач
• 1 большая цель
• 1 навык для развития
• 1 привычка для внедрения

<b>Помни:</b> каждая неделя — это новый шанс стать лучше!
"""
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить цель на неделю", callback_data="goal_create")],
                [InlineKeyboardButton("🔙 К целям", callback_data="goals_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                weekly_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_weekly_goals: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_goals_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику целей."""
    try:
        user = update.effective_user
        if not user:
            return
            
        async with get_db_session() as session:
            user_service = UserService(session)
            goal_service = GoalService(session)
            
            # Получаем пользователя из базы
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.callback_query.answer("❌ Пользователь не найден")
                return
            
            # Получаем статистику целей
            stats = await goal_service.get_user_goals_stats(str(db_user.id))
            
            stats_text = f"""
📊 <b>Статистика целей</b>

<b>Общая статистика:</b>
• Всего целей: {stats.get('total_goals', 0)}
• Выполнено: {stats.get('completed_goals', 0)}
• Активных: {stats.get('active_goals', 0)}
• Процент выполнения: {stats.get('completion_rate', 0):.1f}%

<b>За последний месяц:</b>
• Создано целей: {stats.get('monthly_created', 0)}
• Выполнено целей: {stats.get('monthly_completed', 0)}
• Среднее время выполнения: {stats.get('avg_completion_days', 0):.1f} дней

<b>Анализ:</b>
"""
            
            # Добавляем анализ
            completion_rate = stats.get('completion_rate', 0)
            if completion_rate > 80:
                stats_text += "• Отличная результативность! Ты умеешь достигать целей 🎉\n"
            elif completion_rate > 50:
                stats_text += "• Хорошая результативность! Продолжай в том же духе 👍\n"
            else:
                stats_text += "• Нужно больше фокуса на выполнении целей 📈\n"
            
            active_goals = stats.get('active_goals', 0)
            if active_goals > 5:
                stats_text += "• У тебя много активных целей. Попробуй сфокусироваться на 3-5 главных 🎯\n"
            elif active_goals == 0:
                stats_text += "• Время поставить новые цели! Без целей нет роста 🚀\n"
            else:
                stats_text += "• Оптимальное количество активных целей 👌\n"
            
            keyboard = [
                [InlineKeyboardButton("📈 Детальная статистика", callback_data="goal_stats_detail")],
                [InlineKeyboardButton("🔙 К целям", callback_data="goals_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
    except Exception as e:
        logger.error(f"Ошибка в show_goals_stats: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def complete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отметить цель как выполненную."""
    try:
        goal_id = update.callback_query.data.replace("goal_complete_", "")
        
        user = update.effective_user
        if not user:
            return
            
        async with get_db_session() as session:
            user_service = UserService(session)
            goal_service = GoalService(session)
            activity_service = ActivityService(session)
            
            # Получаем пользователя из базы
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.callback_query.answer("❌ Пользователь не найден")
                return
            
            # Отмечаем цель как выполненную
            success = await goal_service.complete_goal(goal_id)
            if success:
                goal = await goal_service.get_goal_by_id(goal_id)
                
                # Записываем активность
                await activity_service.create_activity(
                    user_id=str(db_user.id),
                    activity_type=ActivityType.GOAL_COMPLETED,
                    description=f"Цель выполнена: {goal.title if goal else 'Неизвестная цель'}"
                )
                
                complete_text = f"""
🎉 <b>Цель выполнена!</b>

✅ {goal.title if goal else 'Цель'}

<b>Поздравляем!</b> Ты сделал еще один шаг к своему развитию.

<b>Что дальше:</b>
• Отметь, что помогло достичь цели
• Поставь новую, более амбициозную цель
• Поделись успехом с сообществом

<b>Помни:</b> каждая выполненная цель делает тебя сильнее! 💪
"""
                
                keyboard = [
                    [InlineKeyboardButton("➕ Новая цель", callback_data="goal_create")],
                    [InlineKeyboardButton("📊 Статистика", callback_data="goal_stats")],
                    [InlineKeyboardButton("🎯 Все цели", callback_data="goals_list")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.edit_message_text(
                    complete_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
                await update.callback_query.answer("🎉 Цель отмечена как выполненная!")
            else:
                await update.callback_query.answer("❌ Не удалось отметить цель")
                
    except Exception as e:
        logger.error(f"Ошибка в complete_goal: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def delete_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удалить цель."""
    try:
        goal_id = update.callback_query.data.replace("goal_delete_", "")
        
        async with get_db_session() as session:
            goal_service = GoalService(session)
            
            # Получаем цель перед удалением
            goal = await goal_service.get_goal_by_id(goal_id)
            if not goal:
                await update.callback_query.answer("❌ Цель не найдена")
                return
            
            # Удаляем цель
            success = await goal_service.delete_goal(goal_id)
            if success:
                await update.callback_query.answer("🗑️ Цель удалена")
                # Возвращаемся к списку целей
                await show_goals_list(update, context)
            else:
                await update.callback_query.answer("❌ Не удалось удалить цель")
                
    except Exception as e:
        logger.error(f"Ошибка в delete_goal: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def skip_goal_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пропустить установку цели."""
    try:
        skip_text = """
⏭️ <b>Постановка цели пропущена</b>

Понимаем, что иногда сложно сформулировать цель сразу.

<b>Помни:</b> цели помогают:
• Направить энергию в нужное русло
• Измерить прогресс
• Сохранить мотивацию
• Структурировать развитие

<b>Ты можешь поставить цель в любое время!</b>

Что хочешь сделать дальше?
"""
        
        keyboard = [
            [InlineKeyboardButton("🎯 Поставить цель", callback_data="goal_create")],
            [InlineKeyboardButton("📊 Статистика целей", callback_data="goal_stats")],
            [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            skip_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в skip_goal_setting: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


# Обработчик сообщений для создания целей
async def handle_goal_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка ввода новой цели."""
    try:
        # Проверяем, ждем ли мы ввода цели
        if not context.user_data.get('waiting_for_goal'):
            return
        
        user = update.effective_user
        if not user:
            return
            
        goal_text = update.message.text.strip()
        if not goal_text:
            await update.message.reply_text("❌ Цель не может быть пустой. Попробуй еще раз.")
            return
        
        async with get_db_session() as session:
            user_service = UserService(session)
            goal_service = GoalService(session)
            activity_service = ActivityService(session)
            
            # Получаем пользователя из базы
            db_user = await user_service.get_user_by_telegram_id(user.id)
            if not db_user:
                await update.message.reply_text("❌ Пользователь не найден")
                return
            
            # Создаем цель
            goal_data = GoalCreate(
                user_id=str(db_user.id),
                title=goal_text,
                description="Цель создана через бота"
            )
            
            goal = await goal_service.create_goal(goal_data)
            
            # Записываем активность
            await activity_service.create_activity(
                user_id=str(db_user.id),
                activity_type=ActivityType.GOAL_CREATED,
                description=f"Создана цель: {goal_text}"
            )
            
            success_text = f"""
✅ <b>Цель создана!</b>

🎯 <b>Твоя новая цель:</b>
{goal_text}

<b>Отлично!</b> Теперь у тебя есть четкая цель для работы.

<b>Следующие шаги:</b>
• Разбей цель на конкретные задачи
• Определи сроки выполнения
• Начни действовать уже сегодня
• Отслеживай прогресс

<b>Помни:</b> путь в тысячу миль начинается с одного шага! 🚀
"""
            
            keyboard = [
                [InlineKeyboardButton("➕ Еще цель", callback_data="goal_create")],
                [InlineKeyboardButton("🎯 Все цели", callback_data="goals_list")],
                [InlineKeyboardButton("🏠 В главное меню", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                success_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Сбрасываем состояние ожидания
            context.user_data.pop('waiting_for_goal', None)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_goal_input: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании цели")
        context.user_data.pop('waiting_for_goal', None)


# Экспорт основного обработчика (уже определен в начале файла)
