"""
Сервис планировщика задач.

Содержит логику планирования и выполнения автоматических задач.
"""

from datetime import datetime, timedelta
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings
from app.core.database import get_database
from app.services.report_service import ReportService
from app.services.goal_service import GoalService
from app.services.telegram_service import TelegramService
from app.services.reminder_service import ReminderService
# from app.services.warmup_service import WarmupService  # Не нужен в ClubBot
# from app.services.product_service import ProductService  # Не нужен в ClubBot
from app.services.ritual_service import RitualService
from app.services.activity_service import ActivityService


class SchedulerService:
    """Сервис планировщика задач."""
    
    def __init__(self, bot: Bot):
        """
        Инициализация сервиса.
        
        Args:
            bot: Экземпляр Telegram бота
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self) -> None:
        """Настройка планируемых задач."""
        try:
            # Ежедневное напоминание об отчете в 21:00
            # Персональные напоминания об отчетах (каждую минуту)
            # Проверяем всех пользователей и отправляем напоминания в их персональное время
            self.scheduler.add_job(
                self.send_daily_report_reminders,
                CronTrigger(minute='*'),  # Каждую минуту
                id='daily_report_reminders',
                name='Персональные напоминания об отчетах'
            )
            
            # Еженедельное напоминание о постановке цели (воскресенье в 10:00)
            self.scheduler.add_job(
                self.send_weekly_goal_reminders,
                CronTrigger(
                    day_of_week=settings.GOAL_DAY_OF_WEEK,
                    hour=10,
                    minute=0
                ),
                id='weekly_goal_reminders',
                name='Еженедельные напоминания о целях'
            )
            
            # Еженедельный анализ активности (воскресенье в 22:00)
            self.scheduler.add_job(
                self.send_weekly_activity_analysis,
                CronTrigger(
                    day_of_week=settings.ANALYTICS_DAY_OF_WEEK,
                    hour=22,
                    minute=0
                ),
                id='weekly_activity_analysis',
                name='Еженедельный анализ активности'
            )
            
            # Отметка пропущенных отчетов (каждый день в 6:00)
            self.scheduler.add_job(
                self.mark_missed_reports,
                CronTrigger(hour=6, minute=0),
                id='mark_missed_reports',
                name='Отметка пропущенных отчетов'
            )
            
            # Напоминание о продлении подписки (каждый день в 12:00)
            self.scheduler.add_job(
                self.send_subscription_reminders,
                CronTrigger(hour=12, minute=0),
                id='subscription_reminders',
                name='Напоминания о продлении подписки'
            )
            
            # Отправка сообщений прогрева (каждые 30 минут)
            self.scheduler.add_job(
                self.send_warmup_messages,
                IntervalTrigger(minutes=30),
                id='warmup_messages',
                name='Отправка сообщений прогрева'
            )
            
            # Отправка дожима офферов (каждые 4 часа)
            self.scheduler.add_job(
                self.send_followup_offers,
                IntervalTrigger(hours=4),
                id='followup_offers',
                name='Отправка дожима офферов'
            )
            
            # Утренние ритуалы (каждые 30 минут с 6:00 до 9:00)
            self.scheduler.add_job(
                self.send_morning_rituals,
                IntervalTrigger(minutes=30),
                id='morning_rituals',
                name='Отправка утренних ритуалов'
            )
            
            # Вечерние ритуалы (каждые 30 минут с 20:00 до 22:00)
            self.scheduler.add_job(
                self.send_evening_rituals,
                IntervalTrigger(minutes=30),
                id='evening_rituals',
                name='Отправка вечерних ритуалов'
            )
            
            # Еженедельные ритуалы (каждый час)
            self.scheduler.add_job(
                self.send_weekly_rituals,
                IntervalTrigger(hours=1),
                id='weekly_rituals',
                name='Отправка еженедельных ритуалов'
            )
            
            # Обработка дневной активности (каждый день в 02:00)
            self.scheduler.add_job(
                self.process_daily_activity,
                CronTrigger(hour=2, minute=0),
                id='daily_activity',
                name='Обработка дневной активности'
            )
            
            # Генерация еженедельных отчетов (воскресенье в 23:00)
            self.scheduler.add_job(
                self.generate_weekly_reports,
                CronTrigger(day_of_week=6, hour=23, minute=0),
                id='weekly_reports',
                name='Генерация еженедельных отчетов'
            )
            
            # Публикация еженедельных отчетов (понедельник в 12:00)
            self.scheduler.add_job(
                self.publish_weekly_reports,
                CronTrigger(day_of_week=0, hour=12, minute=0),
                id='publish_reports',
                name='Публикация еженедельных отчетов'
            )
            
            logger.info("Планировщик задач настроен")
            
        except Exception as e:
            logger.error(f"Ошибка настройки планировщика: {e}")
    
    async def send_daily_report_reminders(self) -> None:
        """Отправка ежедневных персональных напоминаний об отчетах."""
        try:
            logger.info("Начинаем отправку персональных напоминаний об отчетах")
            
            async for session in get_database():
                report_service = ReportService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем текущее время
                now = datetime.now()
                
                # Получаем пользователей, которым нужно отправить напоминания об отчетах в текущее время
                users = await report_service.get_users_for_report_reminder(
                    target_hour=now.hour,
                    target_minute=now.minute
                )
                
                count = 0
                for user in users:
                    try:
                        
                        # Проверяем, не отправили ли уже напоминание сегодня
                        today = datetime.now().date()
                        existing_request = await report_service.get_report_by_date(str(user.id), datetime.now())
                        
                        if existing_request and existing_request.status == "sent":
                            logger.debug(f"Отчет уже отправлен пользователем {user.telegram_id}, пропускаем напоминание")
                            continue
                        
                        # Создаем запрос на отчет (если его нет)
                        if not existing_request:
                            await report_service.create_report_request(str(user.id), datetime.now())
                        
                        # Отправляем напоминание
                        success = await telegram_service.send_report_reminder(user.telegram_id)
                        if success:
                            count += 1
                            logger.info(f"Отправлено напоминание об отчете пользователю {user.telegram_id} в {now.hour:02d}:{now.minute:02d}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания об отчете пользователю {user.telegram_id}: {e}")
                
                logger.info(f"Отправлено {count} напоминаний об отчетах")
                
        except Exception as e:
            logger.error(f"Ошибка отправки персональных напоминаний: {e}")
    
    async def send_weekly_goal_reminders(self) -> None:
        """Отправка еженедельных напоминаний о постановке целей."""
        try:
            logger.info("Начинаем отправку напоминаний о целях")
            
            async for session in get_database():
                goal_service = GoalService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем пользователей для напоминания
                users = await goal_service.get_users_for_goal_reminder()
                
                count = 0
                for user in users:
                    try:
                        # Создаем запрос на цель
                        today = datetime.now()
                        await goal_service.create_goal_request(user.id, today)
                        
                        # Отправляем напоминание
                        success = await telegram_service.send_goal_reminder(user.telegram_id)
                        if success:
                            count += 1
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания о цели пользователю {user.telegram_id}: {e}")
                
                logger.info(f"Отправлено {count} напоминаний о целях")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний о целях: {e}")
    
    async def send_weekly_activity_analysis(self) -> None:
        """Отправка еженедельного анализа активности."""
        try:
            logger.info("Начинаем анализ активности")
            
            async for session in get_database():
                report_service = ReportService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем статистику за прошедшую неделю
                week_start = datetime.now() - timedelta(days=7)
                stats = await report_service.get_weekly_activity_stats(week_start)
                
                # Отправляем отчет админу
                await telegram_service.send_admin_activity_report(stats)
                
                # Отправляем публичный отчет (пока отключено)
                # TODO: добавить отправку в группу когда будет готова
                await telegram_service.send_public_activity_report(stats)
                
                logger.info("Анализ активности завершен")
                
        except Exception as e:
            logger.error(f"Ошибка при анализе активности: {e}")
    
    async def mark_missed_reports(self) -> None:
        """Отметка пропущенных отчетов."""
        try:
            logger.info("Отмечаем пропущенные отчеты")
            
            async for session in get_database():
                report_service = ReportService(session)
                
                # Отмечаем как пропущенные отчеты старше 24 часов
                cutoff_date = datetime.now() - timedelta(hours=24)
                missed_count = await report_service.mark_missed_reports(cutoff_date)
                
                if missed_count > 0:
                    logger.info(f"Отмечено {missed_count} пропущенных отчетов")
                
        except Exception as e:
            logger.error(f"Ошибка при отметке пропущенных отчетов: {e}")
    
    async def send_subscription_reminders(self) -> None:
        """Отправка напоминаний о продлении подписки."""
        try:
            logger.info("Проверяем истекающие подписки")
            
            async for session in get_database():
                reminder_service = ReminderService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем пользователей, которым нужно отправить напоминание
                users_to_remind = await reminder_service.get_users_needing_reminder(days_before=3)
                
                count = 0
                for user in users_to_remind:
                    try:
                        # Формируем сообщение напоминания
                        message_text = await reminder_service.get_reminder_message(user, user.subscription_days_left)
                        
                        # Создаем клавиатуру для продления
                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                        keyboard = [
                            [InlineKeyboardButton("💳 Продлить подписку", callback_data="renew_subscription")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # Отправляем сообщение
                        await self.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message_text,
                            parse_mode="HTML",
                            reply_markup=reply_markup
                        )
                        
                        count += 1
                        logger.info(f"Отправлено напоминание о продлении подписки пользователю {user.telegram_id}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания о подписке пользователю {user.telegram_id}: {e}")
                
                if count > 0:
                    logger.info(f"Отправлено {count} напоминаний о продлении подписки")
                
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминаний о подписке: {e}")
    
    def start(self) -> None:
        """Запуск планировщика."""
        try:
            self.scheduler.start()
            logger.info("Планировщик задач запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")
    
    def stop(self) -> None:
        """Остановка планировщика."""
        try:
            self.scheduler.shutdown()
            logger.info("Планировщик задач остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки планировщика: {e}")
    
    def get_jobs_status(self) -> List[dict]:
        """
        Получение статуса всех задач.
        
        Returns:
            List[dict]: Список информации о задачах
        """
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs_info
    
    async def send_warmup_messages(self) -> None:
        """Отправка сообщений прогрева пользователям."""
        # Прогрев не используется в ClubBot
        logger.info("Прогрев не используется в ClubBot")
        return
        
        # try:
        #     logger.info("Начинаем отправку сообщений прогрева")
        #     
        #     async for session in get_database():
        #         # warmup_service = WarmupService(session)  # Не нужен в ClubBot
        #         telegram_service = TelegramService(self.bot)
        #         
        #         # # Получаем пользователей, готовых к следующему сообщению
        #         # ready_users = await warmup_service.get_users_ready_for_next_message()
        #         
        #         # if not ready_users:
        #         #     logger.debug("Нет пользователей готовых для сообщений прогрева")
        #         #     return
        #         
        #         logger.info(f"Найдено {len(ready_users)} пользователей для отправки сообщений прогрева")
        #         
        #         for user_data in ready_users:
        #             user = user_data['user']
        #             message = user_data['message']
        #             user_warmup = user_data['user_warmup']
        #             
        #             try:
        #                 # Определяем, показывать ли кнопку оффера
        #                 show_offer_button = message.message_type in ['offer', 'follow_up']
        #                 
        #                 # Отправляем сообщение
        #                 success = await telegram_service.send_warmup_message(
        #                     chat_id=user.telegram_id,
        #                     message_title=message.title,
        #                     message_text=message.text,
        #                     show_offer_button=show_offer_button
        #                 )
        #                 
        #                 # Отмечаем сообщение как отправленное
        #                 await warmup_service.mark_message_sent(
        #                     user_id=str(user.id),
        #                     warmup_message_id=str(message.id),
        #                     success=success
        #                 )
        #                 
        #                 if success:
        #                     logger.info(f"Отправлено сообщение прогрева пользователю {user.telegram_id}: {message.title}")
        #                 else:
        #                     logger.warning(f"Не удалось отправить сообщение прогрева пользователю {user.telegram_id}")
        #                     
        #             except Exception as e:
        #                 logger.error(f"Ошибка отправки сообщения прогрева пользователю {user.telegram_id}: {e}")
        #                 
        #                 # Отмечаем как неудачную отправку
        #                 await warmup_service.mark_message_sent(
        #                     user_id=str(user.id),
        #                     warmup_message_id=str(message.id),
        #                     success=False,
        #                     error_message=str(e)
        #                 )
        #         
        #         logger.info(f"Обработано {len(ready_users)} сообщений прогрева")
        #         break  # Выходим после первой сессии
        #         
        # except Exception as e:
        #     logger.error(f"Ошибка отправки сообщений прогрева: {e}")
    
    async def send_followup_offers(self) -> None:
        """Отправка дожима офферов пользователям."""
        # Дожим офферов не используется в ClubBot
        logger.info("Дожим офферов не используется в ClubBot")
        return
        
        # try:
        #     logger.info("Начинаем отправку дожима офферов")
        #     
        #     async for session in get_database():
        #         # product_service = ProductService(session)  # Не нужен в ClubBot
        #         telegram_service = TelegramService(self.bot)
        #         
        #         # Получаем пользователей для дожима (48 часов после показа оффера)
        #         users_for_followup = await product_service.get_users_for_followup_offers(hours_since_show=48)
        #         
        #         if not users_for_followup:
        #             logger.debug("Нет пользователей для дожима офферов")
        #             return
        #         
        #         logger.info(f"Найдено {len(users_for_followup)} пользователей для дожима офферов")
        #         
        #         for user_data in users_for_followup:
        #             user = user_data['user']
        #             offer = user_data['offer']
        #             product = user_data['product']
        #             user_offer = user_data['user_offer']
        #             
        #             try:
        #                 # Получаем дожим оффер (второй оффер для того же продукта)
        #                 followup_offer = await self._get_followup_offer(session, product.id.hex)
        #                 
        #                 if not followup_offer:
        #                     logger.warning(f"Дожим оффер не найден для продукта {product.name}")
        #                     continue
        #                 
        #                 # Отправляем дожим сообщение
        #                 success = await telegram_service.send_warmup_message(
        #                     chat_id=user.telegram_id,
        #                     message_title=f"Последний шанс: {product.name}",
        #                     message_text=followup_offer.text,
        #                     show_offer_button=True
        #                 )
        #                 
        #                 if success:
        #                     # Отмечаем отправку дожима
        #                     await product_service.mark_followup_sent(
        #                         user_id=str(user.id),
        #                         offer_id=followup_offer.id.hex
        #                     )
        #                     
        #                     logger.info(f"Отправлен дожим пользователю {user.telegram_id} для продукта {product.name}")
        #                 else:
        #                     logger.warning(f"Не удалось отправить дожим пользователю {user.telegram_id}")
        #                     
        #             except Exception as e:
        #                 logger.error(f"Ошибка отправки дожима пользователю {user.telegram_id}: {e}")
        #         
        #         logger.info(f"Обработано {len(users_for_followup)} дожимов офферов")
        #         break  # Выходим после первой сессии
        #         
        # except Exception as e:
        #     logger.error(f"Ошибка отправки дожима офферов: {e}")
    
    async def _get_followup_offer(self, session: AsyncSession, product_id: str):
        """Получить дожим оффер для продукта."""
        # ProductOffer не используется в ClubBot
        return None
    
    async def send_morning_rituals(self) -> None:
        """Отправка утренних ритуалов пользователям."""
        try:
            current_time = datetime.now()
            
            # Ограничиваем отправку утром (6:00-9:00)
            if not (6 <= current_time.hour <= 9):
                return
            
            async with get_database() as session:
                ritual_service = RitualService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем пользователей для утренних ритуалов
                from app.models.ritual import RitualType
                users_to_send = await ritual_service.get_users_for_ritual_sending(
                    RitualType.MORNING, current_time
                )
                
                logger.info(f"Найдено {len(users_to_send)} пользователей для утренних ритуалов")
                
                for user_data in users_to_send:
                    user = user_data['user']
                    user_ritual = user_data['user_ritual']
                    ritual = user_data['ritual']
                    
                    # Парсим кнопки ритуала
                    buttons = await ritual_service.parse_response_buttons(ritual.response_buttons)
                    buttons_data = [button.dict() for button in buttons] if buttons else None
                    
                    # Отправляем ритуал
                    success = await telegram_service.send_ritual_message(
                        chat_id=user.telegram_id,
                        ritual_title=ritual.message_title,
                        ritual_text=ritual.message_text,
                        buttons=buttons_data,
                        user_ritual_id=user_ritual.id.hex,
                        ritual_id=ritual.id.hex
                    )
                    
                    if success:
                        # Отмечаем отправку
                        await ritual_service.mark_ritual_sent(user_ritual.id.hex, current_time)
                        logger.debug(f"Утренний ритуал отправлен пользователю {user.telegram_id}")
                    
                logger.info(f"Обработано {len(users_to_send)} пользователей для утренних ритуалов")
                
        except Exception as e:
            logger.error(f"Ошибка отправки утренних ритуалов: {e}")
    
    async def send_evening_rituals(self) -> None:
        """Отправка вечерних ритуалов пользователям."""
        try:
            current_time = datetime.now()
            
            # Ограничиваем отправку вечером (20:00-22:00)
            if not (20 <= current_time.hour <= 22):
                return
            
            async with get_database() as session:
                ritual_service = RitualService(session)
                telegram_service = TelegramService(self.bot)
                
                # Получаем пользователей для вечерних ритуалов
                from app.models.ritual import RitualType
                users_to_send = await ritual_service.get_users_for_ritual_sending(
                    RitualType.EVENING, current_time
                )
                
                logger.info(f"Найдено {len(users_to_send)} пользователей для вечерних ритуалов")
                
                for user_data in users_to_send:
                    user = user_data['user']
                    user_ritual = user_data['user_ritual']
                    ritual = user_data['ritual']
                    
                    # Парсим кнопки ритуала
                    buttons = await ritual_service.parse_response_buttons(ritual.response_buttons)
                    buttons_data = [button.dict() for button in buttons] if buttons else None
                    
                    # Отправляем ритуал
                    success = await telegram_service.send_ritual_message(
                        chat_id=user.telegram_id,
                        ritual_title=ritual.message_title,
                        ritual_text=ritual.message_text,
                        buttons=buttons_data,
                        user_ritual_id=user_ritual.id.hex,
                        ritual_id=ritual.id.hex
                    )
                    
                    if success:
                        # Отмечаем отправку
                        await ritual_service.mark_ritual_sent(user_ritual.id.hex, current_time)
                        logger.debug(f"Вечерний ритуал отправлен пользователю {user.telegram_id}")
                    
                logger.info(f"Обработано {len(users_to_send)} пользователей для вечерних ритуалов")
                
        except Exception as e:
            logger.error(f"Ошибка отправки вечерних ритуалов: {e}")
    
    async def send_weekly_rituals(self) -> None:
        """Отправка еженедельных ритуалов пользователям."""
        try:
            current_time = datetime.now()
            
            async with get_database() as session:
                ritual_service = RitualService(session)
                telegram_service = TelegramService(self.bot)
                
                # Проверяем все типы еженедельных ритуалов
                from app.models.ritual import RitualType
                weekly_types = [
                    RitualType.WEEKLY_CHALLENGE,
                    RitualType.WEEKLY_GOALS, 
                    RitualType.FRIDAY_CYCLE
                ]
                
                total_sent = 0
                
                for ritual_type in weekly_types:
                    users_to_send = await ritual_service.get_users_for_ritual_sending(
                        ritual_type, current_time
                    )
                    
                    logger.debug(f"Найдено {len(users_to_send)} пользователей для {ritual_type}")
                    
                    for user_data in users_to_send:
                        user = user_data['user']
                        user_ritual = user_data['user_ritual']
                        ritual = user_data['ritual']
                        
                        # Парсим кнопки ритуала
                        buttons = await ritual_service.parse_response_buttons(ritual.response_buttons)
                        buttons_data = [button.dict() for button in buttons] if buttons else None
                        
                        # Отправляем ритуал
                        success = await telegram_service.send_ritual_message(
                            chat_id=user.telegram_id,
                            ritual_title=ritual.message_title,
                            ritual_text=ritual.message_text,
                            buttons=buttons_data,
                            user_ritual_id=user_ritual.id.hex,
                            ritual_id=ritual.id.hex
                        )
                        
                        if success:
                            # Отмечаем отправку
                            await ritual_service.mark_ritual_sent(user_ritual.id.hex, current_time)
                            logger.debug(f"Еженедельный ритуал {ritual_type} отправлен пользователю {user.telegram_id}")
                            total_sent += 1
                
                if total_sent > 0:
                    logger.info(f"Отправлено {total_sent} еженедельных ритуалов")
                
        except Exception as e:
            logger.error(f"Ошибка отправки еженедельных ритуалов: {e}")
    
    async def process_daily_activity(self) -> None:
        """Обработка дневной активности пользователей."""
        try:
            async with get_database() as session:
                activity_service = ActivityService(session)
                
                # Обрабатываем активность за вчерашний день
                from datetime import date, timedelta
                yesterday = date.today() - timedelta(days=1)
                
                await activity_service.process_daily_activities(yesterday)
                
                logger.info(f"Обработана дневная активность за {yesterday}")
                
        except Exception as e:
            logger.error(f"Ошибка обработки дневной активности: {e}")
    
    async def generate_weekly_reports(self) -> None:
        """Генерация еженедельных отчетов активности."""
        try:
            async with get_database() as session:
                activity_service = ActivityService(session)
                
                # Генерируем отчет за прошедшую неделю
                from datetime import date, timedelta
                today = date.today()
                # Находим понедельник прошлой недели
                days_since_monday = today.weekday()
                last_monday = today - timedelta(days=days_since_monday + 7)
                
                report = await activity_service.generate_weekly_report(last_monday)
                
                logger.info(f"Сгенерирован еженедельный отчет за {last_monday}")
                
        except Exception as e:
            logger.error(f"Ошибка генерации еженедельных отчетов: {e}")
    
    async def publish_weekly_reports(self) -> None:
        """Публикация еженедельных отчетов в группе."""
        try:
            async with get_database() as session:
                from sqlalchemy import select, and_
                from app.models.activity import WeeklyReport
                from datetime import date, timedelta
                
                # Находим неопубликованные отчеты за последнюю неделю
                today = date.today()
                week_ago = today - timedelta(days=7)
                
                stmt = select(WeeklyReport).where(
                    and_(
                        WeeklyReport.is_published == False,
                        WeeklyReport.week_start_date >= week_ago
                    )
                ).order_by(WeeklyReport.week_start_date.desc())
                
                result = await session.execute(stmt)
                reports = result.scalars().all()
                
                telegram_service = TelegramService(self.bot)
                
                for report in reports:
                    try:
                        # Отправляем отчет в группу
                        success = await telegram_service.send_message_to_group(
                            settings.telegram_group_id,
                            report.report_message
                        )
                        
                        if success:
                            # Отмечаем как опубликованный
                            report.is_published = True
                            report.published_at = datetime.now()
                            
                            logger.info(f"Опубликован еженедельный отчет за {report.week_start_date}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка публикации отчета {report.id}: {e}")
                
                await session.commit()
                logger.info(f"Обработано {len(reports)} еженедельных отчетов")
                
        except Exception as e:
            logger.error(f"Ошибка публикации еженедельных отчетов: {e}")
