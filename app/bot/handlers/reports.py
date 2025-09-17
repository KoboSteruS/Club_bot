"""
Обработчик отчетов для ClubBot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import date

from ...services.user_service import UserService
from ...services.report_service import ReportService
from ...services.activity_service import ActivityService, ActivityType
from ...models.report import ReportStatus
from ..keyboards.main import get_reports_keyboard


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик отчетов."""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "reports_my":
            await show_reports_menu(update, context)
        elif query.data == "report_write":
            await start_report_writing(update, context)
        elif query.data == "report_stats":
            await show_report_stats(update, context)
        elif query.data == "report_history":
            await show_report_history(update, context)
        elif query.data == "report_submit":
            await submit_report(update, context)
        elif query.data == "report_skip":
            await skip_report(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка в report_handler: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню отчетов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        report_service = ReportService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем статистику отчетов
        stats = await report_service.get_user_activity_stats(str(db_user.id), 30)
        
        reports_text = f"""
📊 <b>Мои отчеты</b>

<b>Статистика за 30 дней:</b>
• Отправлено отчетов: {stats.get('submitted_reports', 0)}
• Пропущено отчетов: {stats.get('skipped_reports', 0)}
• Общее количество слов: {stats.get('total_words', 0)}
• Процент отправки: {stats.get('submission_rate', 0):.1f}%

<b>Среднее количество слов в отчете:</b> {stats.get('avg_words_per_report', 0):.0f}

<b>Что ты можешь сделать:</b>
• Написать новый отчет
• Посмотреть историю отчетов
• Изучить свою статистику

Выбери действие:
"""
        
        keyboard = get_reports_keyboard()
        
        await update.callback_query.edit_message_text(
            reports_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_reports_menu: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def start_report_writing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать написание отчета."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        report_service = ReportService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Проверяем, есть ли уже отчет на сегодня
        today_reports = await report_service.get_pending_reports(date.today())
        user_today_report = None
        
        for report in today_reports:
            if str(report.user_id) == str(db_user.id):
                user_today_report = report
                break
        
        if user_today_report:
            # Показываем существующий отчет
            report_text = f"""
📝 <b>Отчет на {date.today().strftime('%d.%m.%Y')}</b>

<b>Статус:</b> {user_today_report.status_display}

<b>Содержимое:</b>
{user_today_report.content or 'Отчет еще не написан'}

<b>Количество слов:</b> {user_today_report.word_count}

Что хочешь сделать с отчетом?
"""
            
            keyboard = [
                [InlineKeyboardButton("✏️ Редактировать", callback_data="report_edit")],
                [InlineKeyboardButton("📊 Статистика", callback_data="report_stats")],
                [InlineKeyboardButton("🔙 Назад", callback_data="reports_my")]
            ]
        else:
            # Создаем новый отчет
            report = await report_service.create_report(
                user_id=str(db_user.id),
                report_type=ReportType.DAILY,
                report_date=date.today()
            )
            
            # Сохраняем ID отчета в контексте
            context.user_data['current_report_id'] = str(report.id)
            
            report_text = f"""
📝 <b>Написание отчета</b>

<b>Дата:</b> {date.today().strftime('%d.%m.%Y')}

<b>Время подвести итог дня</b>

Напиши, что прожил, что понял, где дотянул, где сдался.

<b>Это поможет тебе:</b>
• Осознать свой прогресс
• Выявить точки роста
• Сохранить мотивацию
• Остаться в ритме

<b>Примеры тем для отчета:</b>
• Что получилось сегодня?
• Какие были трудности?
• Что нового узнал?
• Как продвинулся к целям?
• За что благодарен?

<b>Напиши свой отчет:</b>
"""
            
            keyboard = [
                [InlineKeyboardButton("📝 Отправить отчет", callback_data="report_submit")],
                [InlineKeyboardButton("😐 Пропустить", callback_data="report_skip")],
                [InlineKeyboardButton("🔙 Назад", callback_data="reports_my")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            report_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в start_report_writing: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def submit_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправить отчет."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID отчета из контекста
        report_id = context.user_data.get('current_report_id')
        if not report_id:
            await update.callback_query.answer("❌ Отчет не найден")
            return
        
        # Получаем сервисы
        report_service = ReportService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        user_service = UserService(context.bot_data.get('session'))
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Показываем форму для ввода отчета
        submit_text = """
📝 <b>Отправка отчета</b>

Напиши свой отчет о прошедшем дне.

<b>Советы для хорошего отчета:</b>
• Будь честным с собой
• Опиши конкретные события
• Поделись эмоциями и мыслями
• Отметь прогресс и трудности
• Поблагодари за что-то хорошее

<b>Минимум:</b> 50 слов
<b>Рекомендуется:</b> 100-300 слов

<b>Напиши свой отчет:</b>
"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="report_write")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            submit_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Устанавливаем состояние ожидания отчета
        context.user_data['waiting_for_report'] = True
        
    except Exception as e:
        logger.error(f"Ошибка в submit_report: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def skip_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пропустить отчет."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем ID отчета из контекста
        report_id = context.user_data.get('current_report_id')
        if not report_id:
            await update.callback_query.answer("❌ Отчет не найден")
            return
        
        # Получаем сервисы
        report_service = ReportService(context.bot_data.get('session'))
        activity_service = ActivityService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        user_service = UserService(context.bot_data.get('session'))
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Пропускаем отчет
        await report_service.skip_report(report_id)
        
        # Записываем активность
        await activity_service.create_activity(
            user_id=str(db_user.id),
            activity_type=ActivityType.REPORT_SUBMITTED,
            description="Отчет пропущен"
        )
        
        skip_text = """
😐 <b>Отчет пропущен</b>

Понимаем, что иногда бывает сложно подвести итоги дня.

<b>Помни:</b> отчеты помогают:
• Осознать свой прогресс
• Выявить точки роста
• Сохранить мотивацию
• Остаться в ритме

<b>Ты можешь написать отчет в любое время</b>

Что хочешь сделать дальше?
"""
        
        keyboard = [
            [InlineKeyboardButton("📝 Написать отчет", callback_data="report_write")],
            [InlineKeyboardButton("📊 Статистика", callback_data="report_stats")],
            [InlineKeyboardButton("🔙 Назад", callback_data="reports_my")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            skip_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        # Очищаем данные из контекста
        context.user_data.pop('current_report_id', None)
        context.user_data.pop('waiting_for_report', None)
        
    except Exception as e:
        logger.error(f"Ошибка в skip_report: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_report_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику отчетов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        report_service = ReportService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем статистику
        stats = await report_service.get_user_activity_stats(str(db_user.id), 30)
        
        stats_text = f"""
📊 <b>Статистика отчетов</b>

<b>За последние 30 дней:</b>

📝 <b>Отчеты:</b>
• Отправлено: {stats.get('submitted_reports', 0)}
• Пропущено: {stats.get('skipped_reports', 0)}
• Всего: {stats.get('total_reports', 0)}

📈 <b>Активность:</b>
• Процент отправки: {stats.get('submission_rate', 0):.1f}%
• Общее количество слов: {stats.get('total_words', 0)}
• Среднее слов в отчете: {stats.get('avg_words_per_report', 0):.0f}

<b>Рекомендации:</b>
"""
        
        # Добавляем рекомендации
        if stats.get('submission_rate', 0) < 50:
            stats_text += "• Старайся писать отчеты чаще\n"
        elif stats.get('submission_rate', 0) < 80:
            stats_text += "• Хорошая активность! Продолжай в том же духе\n"
        else:
            stats_text += "• Отличная активность! Ты на правильном пути\n"
        
        if stats.get('avg_words_per_report', 0) < 50:
            stats_text += "• Попробуй писать более подробные отчеты\n"
        elif stats.get('avg_words_per_report', 0) > 300:
            stats_text += "• Очень подробные отчеты! Молодец\n"
        else:
            stats_text += "• Оптимальная длина отчетов\n"
        
        keyboard = [
            [InlineKeyboardButton("📝 Написать отчет", callback_data="report_write")],
            [InlineKeyboardButton("📋 История отчетов", callback_data="report_history")],
            [InlineKeyboardButton("🔙 Назад", callback_data="reports_my")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_report_stats: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


async def show_report_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать историю отчетов."""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Получаем сервисы
        user_service = UserService(context.bot_data.get('session'))
        report_service = ReportService(context.bot_data.get('session'))
        
        # Получаем пользователя из базы
        db_user = await user_service.get_user_by_telegram_id(user.id)
        if not db_user:
            await update.callback_query.answer("❌ Пользователь не найден")
            return
        
        # Получаем последние отчеты
        reports = await report_service.get_user_reports(str(db_user.id), 7)
        
        if not reports:
            history_text = """
📋 <b>История отчетов</b>

<b>За последние 7 дней:</b>

📭 Отчетов не найдено

<b>Начни писать отчеты, чтобы отслеживать свой прогресс!</b>
"""
        else:
            history_text = """
📋 <b>История отчетов</b>

<b>За последние 7 дней:</b>

"""
            
            for report in reports[:5]:  # Показываем только последние 5
                status_emoji = "✅" if report.is_submitted else "⏭️" if report.is_skipped else "⏳"
                history_text += f"{status_emoji} {report.report_date.strftime('%d.%m')} - {report.status_display}\n"
                
                if report.is_submitted and report.content:
                    # Показываем первые 50 символов
                    preview = report.content[:50] + "..." if len(report.content) > 50 else report.content
                    history_text += f"   📝 {preview}\n"
                
                history_text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("📝 Написать отчет", callback_data="report_write")],
            [InlineKeyboardButton("📊 Статистика", callback_data="report_stats")],
            [InlineKeyboardButton("🔙 Назад", callback_data="reports_my")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            history_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_report_history: {e}")
        await update.callback_query.answer("❌ Произошла ошибка")


# Экспорт основного обработчика (уже определен в начале файла)
