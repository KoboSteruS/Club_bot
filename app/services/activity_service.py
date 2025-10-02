"""
Сервис для отслеживания и анализа активности пользователей в чатах.

Этот модуль содержит логику для:
- Отслеживания активности в группах
- Анализа статистики сообщений
- Генерации рейтингов пользователей
- Создания еженедельных отчетов
"""

import json
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import AsyncSession
from app.core.exceptions import BaseException
from app.models import (
    ChatActivity, UserActivity, ActivitySummary, WeeklyReport, User,
    ActivityType, ActivityPeriod
)
from app.schemas.activity import (
    ChatActivityCreate, UserActivityCreate, WeeklyReportCreate,
    TopUserSchema, ActivityStatsResponse, UserActivityFilter
)


class ActivityException(BaseException):
    """Исключение для ошибок системы активности."""
    pass


class ActivityService:
    """Сервис для управления активностью пользователей."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def record_activity(self, activity_data: ChatActivityCreate) -> ChatActivity:
        """Записать активность пользователя в чате."""
        try:
            activity = ChatActivity(
                user_id=activity_data.user_id,
                chat_id=activity_data.chat_id,
                message_id=activity_data.message_id,
                activity_type=activity_data.activity_type,
                message_text=activity_data.message_text,
                message_length=activity_data.message_length,
                activity_date=activity_data.activity_date,
                activity_hour=activity_data.activity_hour,
                is_reply=activity_data.is_reply,
                is_forward=activity_data.is_forward,
                reply_to_user_id=activity_data.reply_to_user_id,
                media_file_id=activity_data.media_file_id,
                media_duration=activity_data.media_duration,
                media_file_size=activity_data.media_file_size
            )
            
            self.session.add(activity)
            await self.session.commit()
            await self.session.refresh(activity)
            
            logger.debug(f"Записана активность пользователя {activity_data.user_id}: {activity_data.activity_type}")
            return activity
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка записи активности: {e}")
            raise ActivityException(f"Не удалось записать активность: {e}")
    
    # Алиас для совместимости
    create_chat_activity = record_activity
    
    async def get_user_activity_stats(self, user_id: str, period_type: ActivityPeriod, 
                                    start_date: date, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Получить статистику активности пользователя за период."""
        try:
            if not end_date:
                end_date = start_date
            
            # Базовый запрос
            stmt = (
                select(
                    func.count(ChatActivity.id).label('total_messages'),
                    func.sum(ChatActivity.message_length).label('total_characters'),
                    func.avg(ChatActivity.message_length).label('avg_message_length'),
                    func.sum(ChatActivity.is_reply.cast('INTEGER')).label('replies_sent'),
                    func.sum(ChatActivity.is_forward.cast('INTEGER')).label('forwards_sent'),
                    func.count(func.distinct(ChatActivity.activity_hour)).label('active_hours')
                )
                .where(
                    and_(
                        ChatActivity.user_id == user_id,
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            stats = result.first()
            
            # Статистика по типам активности
            type_stmt = (
                select(
                    ChatActivity.activity_type,
                    func.count(ChatActivity.id).label('count')
                )
                .where(
                    and_(
                        ChatActivity.user_id == user_id,
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
                .group_by(ChatActivity.activity_type)
            )
            
            type_result = await self.session.execute(type_stmt)
            activity_by_type = {row.activity_type: row.count for row in type_result}
            
            # Статистика по часам
            hour_stmt = (
                select(
                    ChatActivity.activity_hour,
                    func.count(ChatActivity.id).label('count')
                )
                .where(
                    and_(
                        ChatActivity.user_id == user_id,
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
                .group_by(ChatActivity.activity_hour)
                .order_by(desc('count'))
            )
            
            hour_result = await self.session.execute(hour_stmt)
            activity_by_hour = {row.activity_hour: row.count for row in hour_result}
            most_active_hour = list(activity_by_hour.keys())[0] if activity_by_hour else None
            
            # Вычисляем балл активности
            activity_score = self._calculate_activity_score(
                stats.total_messages or 0,
                stats.total_characters or 0,
                stats.replies_sent or 0,
                activity_by_type
            )
            
            return {
                'total_messages': stats.total_messages or 0,
                'total_characters': stats.total_characters or 0,
                'average_message_length': round(stats.avg_message_length or 0, 1),
                'replies_sent': stats.replies_sent or 0,
                'forwards_sent': stats.forwards_sent or 0,
                'active_hours': stats.active_hours or 0,
                'most_active_hour': most_active_hour,
                'activity_by_type': activity_by_type,
                'activity_by_hour': activity_by_hour,
                'activity_score': activity_score
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики активности: {e}")
            return {}
    
    def _calculate_activity_score(self, messages: int, characters: int, 
                                replies: int, activity_by_type: Dict[str, int]) -> int:
        """Вычислить балл активности пользователя."""
        try:
            score = 0
            
            # Базовые очки за сообщения
            score += messages * 1
            
            # Бонус за символы (каждые 100 символов = 1 очко)
            score += (characters // 100)
            
            # Бонус за ответы (показатель вовлеченности)
            score += replies * 2
            
            # Бонусы за разные типы активности
            type_bonuses = {
                ActivityType.MESSAGE: 1,
                ActivityType.PHOTO: 2,
                ActivityType.VIDEO: 3,
                ActivityType.VOICE: 3,
                ActivityType.DOCUMENT: 2,
                ActivityType.POLL: 5,
                ActivityType.REPLY: 2
            }
            
            for activity_type, count in activity_by_type.items():
                bonus = type_bonuses.get(activity_type, 1)
                score += count * bonus
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления балла активности: {e}")
            return 0
    
    async def update_user_activity_summary(self, user_id: str, period_type: ActivityPeriod, 
                                         period_date: date) -> UserActivity:
        """Обновить сводную активность пользователя за период."""
        try:
            # Получаем статистику
            stats = await self.get_user_activity_stats(user_id, period_type, period_date)
            
            # Ищем существующую запись
            stmt = select(UserActivity).where(
                and_(
                    UserActivity.user_id == user_id,
                    UserActivity.period_type == period_type,
                    UserActivity.period_date == period_date
                )
            )
            result = await self.session.execute(stmt)
            user_activity = result.scalar_one_or_none()
            
            if user_activity:
                # Обновляем существующую
                user_activity.total_messages = stats.get('total_messages', 0)
                user_activity.total_characters = stats.get('total_characters', 0)
                user_activity.average_message_length = int(stats.get('average_message_length', 0))
                user_activity.most_active_hour = stats.get('most_active_hour')
                user_activity.replies_sent = stats.get('replies_sent', 0)
                user_activity.forwards_sent = stats.get('forwards_sent', 0)
                user_activity.activity_score = stats.get('activity_score', 0)
                user_activity.activity_hours = json.dumps(stats.get('activity_by_hour', {}))
                
                # Подсчитываем медиа сообщения
                activity_by_type = stats.get('activity_by_type', {})
                media_types = [ActivityType.PHOTO, ActivityType.VIDEO, ActivityType.VOICE, 
                              ActivityType.DOCUMENT, ActivityType.STICKER]
                user_activity.media_messages = sum(
                    activity_by_type.get(t, 0) for t in media_types
                )
                user_activity.text_messages = activity_by_type.get(ActivityType.MESSAGE, 0)
                
            else:
                # Создаем новую
                activity_by_type = stats.get('activity_by_type', {})
                media_types = [ActivityType.PHOTO, ActivityType.VIDEO, ActivityType.VOICE, 
                              ActivityType.DOCUMENT, ActivityType.STICKER]
                
                user_activity = UserActivity(
                    user_id=user_id,
                    period_type=period_type,
                    period_date=period_date,
                    total_messages=stats.get('total_messages', 0),
                    text_messages=activity_by_type.get(ActivityType.MESSAGE, 0),
                    media_messages=sum(activity_by_type.get(t, 0) for t in media_types),
                    total_characters=stats.get('total_characters', 0),
                    average_message_length=int(stats.get('average_message_length', 0)),
                    most_active_hour=stats.get('most_active_hour'),
                    activity_hours=json.dumps(stats.get('activity_by_hour', {})),
                    replies_sent=stats.get('replies_sent', 0),
                    forwards_sent=stats.get('forwards_sent', 0),
                    activity_score=stats.get('activity_score', 0)
                )
                self.session.add(user_activity)
            
            await self.session.commit()
            await self.session.refresh(user_activity)
            
            logger.debug(f"Обновлена сводная активность пользователя {user_id} за {period_date}")
            return user_activity
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления сводной активности: {e}")
            raise ActivityException(f"Не удалось обновить активность: {e}")
    
    async def get_top_users(self, period_type: ActivityPeriod, period_date: date, 
                          limit: int = 10) -> List[TopUserSchema]:
        """Получить топ активных пользователей за период."""
        try:
            stmt = (
                select(UserActivity, User)
                .join(User, UserActivity.user_id == User.id)
                .where(
                    and_(
                        UserActivity.period_type == period_type,
                        UserActivity.period_date == period_date,
                        UserActivity.total_messages > 0
                    )
                )
                .order_by(desc(UserActivity.activity_score))
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            rows = result.all()
            
            top_users = []
            for rank, (user_activity, user) in enumerate(rows, 1):
                top_users.append(TopUserSchema(
                    user_id=user_activity.user_id,
                    telegram_id=user.telegram_id,
                    username=user.username,
                    first_name=user.first_name,
                    display_name=user.display_name,
                    total_messages=user_activity.total_messages,
                    activity_score=user_activity.activity_score,
                    rank=rank
                ))
            
            # Обновляем ранги в базе
            for rank, (user_activity, _) in enumerate(rows, 1):
                user_activity.period_rank = rank
            
            await self.session.commit()
            
            logger.info(f"Получен топ {len(top_users)} пользователей за {period_date}")
            return top_users
            
        except Exception as e:
            logger.error(f"Ошибка получения топа пользователей: {e}")
            return []
    
    async def generate_weekly_report(self, week_start: date) -> WeeklyReport:
        """Сгенерировать еженедельный отчет активности."""
        try:
            week_end = week_start + timedelta(days=6)
            
            # Получаем топ активных пользователей
            top_users = await self.get_top_users(
                ActivityPeriod.WEEKLY, week_start, limit=3
            )
            
            # Получаем подключающихся пользователей (с низкой но растущей активностью)
            connecting_users = await self._get_connecting_users(week_start, limit=3)
            
            # Общая статистика
            total_participants = await self._get_total_participants(week_start, week_end)
            active_participants = len(top_users) + len(connecting_users)
            activity_percentage = int((active_participants / max(total_participants, 1)) * 100)
            
            # Формируем сообщение для публикации
            report_message = await self._format_weekly_report_message(
                top_users, connecting_users, week_start, week_end
            )
            
            # Создаем отчет
            weekly_report = WeeklyReport(
                week_start_date=week_start,
                week_end_date=week_end,
                top_active_users=json.dumps([user.dict() for user in top_users]),
                connecting_users=json.dumps([user.dict() for user in connecting_users]),
                total_participants=total_participants,
                active_participants=active_participants,
                activity_percentage=activity_percentage,
                report_message=report_message
            )
            
            self.session.add(weekly_report)
            await self.session.commit()
            await self.session.refresh(weekly_report)
            
            logger.info(f"Создан еженедельный отчет за {week_start} - {week_end}")
            return weekly_report
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания еженедельного отчета: {e}")
            raise ActivityException(f"Не удалось создать отчет: {e}")
    
    async def _get_connecting_users(self, week_start: date, limit: int) -> List[TopUserSchema]:
        """Получить подключающихся пользователей (с ростом активности)."""
        try:
            # Пользователи с активностью за текущую неделю, но не в топе
            stmt = (
                select(UserActivity, User)
                .join(User, UserActivity.user_id == User.id)
                .where(
                    and_(
                        UserActivity.period_type == ActivityPeriod.WEEKLY,
                        UserActivity.period_date == week_start,
                        UserActivity.total_messages > 0,
                        UserActivity.total_messages < 10,  # Не слишком активные
                        or_(
                            UserActivity.period_rank.is_(None),
                            UserActivity.period_rank > 3
                        )
                    )
                )
                .order_by(desc(UserActivity.activity_score))
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            rows = result.all()
            
            connecting_users = []
            for user_activity, user in rows:
                connecting_users.append(TopUserSchema(
                    user_id=user_activity.user_id,
                    telegram_id=user.telegram_id,
                    username=user.username,
                    first_name=user.first_name,
                    display_name=user.display_name,
                    total_messages=user_activity.total_messages,
                    activity_score=user_activity.activity_score,
                    rank=0  # Не ранжируются
                ))
            
            return connecting_users
            
        except Exception as e:
            logger.error(f"Ошибка получения подключающихся пользователей: {e}")
            return []
    
    async def _get_total_participants(self, week_start: date, week_end: date) -> int:
        """Получить общее количество участников за неделю."""
        try:
            stmt = (
                select(func.count(func.distinct(ChatActivity.user_id)))
                .where(
                    and_(
                        ChatActivity.activity_date >= week_start,
                        ChatActivity.activity_date <= week_end
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Ошибка подсчета участников: {e}")
            return 0
    
    async def _format_weekly_report_message(self, top_users: List[TopUserSchema], 
                                          connecting_users: List[TopUserSchema],
                                          week_start: date, week_end: date) -> str:
        """Форматировать сообщение еженедельного отчета."""
        try:
            message_parts = []
            
            # Заголовок
            message_parts.append(f"📊 <b>ОТЧЕТ ЗА НЕДЕЛЮ</b>")
            message_parts.append(f"📅 {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}")
            message_parts.append("")
            
            # Топ включенных
            if top_users:
                message_parts.append("🔥 <b>Топ включённых:</b>")
                for user in top_users:
                    name = user.display_name
                    if user.username and not name.startswith('@'):
                        name = f"@{user.username}"
                    message_parts.append(f"   {user.rank}. {name} ({user.total_messages} сообщений)")
                message_parts.append("")
            
            # Подключающиеся
            if connecting_users:
                message_parts.append("💪 <b>Подключаемся:</b>")
                for user in connecting_users:
                    name = user.display_name
                    if user.username and not name.startswith('@'):
                        name = f"@{user.username}"
                    message_parts.append(f"   • {name}")
                message_parts.append("")
            
            # Мотивационное сообщение
            message_parts.append("🎯 <b>Помни:</b> активность в чате — это инвестиция в свой рост!")
            message_parts.append("🚀 Делись опытом, задавай вопросы, поддерживай других!")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Ошибка форматирования отчета: {e}")
            return "Ошибка формирования отчета"
    
    async def process_daily_activities(self, target_date: Optional[date] = None) -> None:
        """Обработать дневные активности и обновить сводки."""
        try:
            if not target_date:
                target_date = date.today() - timedelta(days=1)  # Вчерашний день
            
            # Получаем всех пользователей с активностью за день
            stmt = (
                select(func.distinct(ChatActivity.user_id))
                .where(ChatActivity.activity_date == target_date)
            )
            
            result = await self.session.execute(stmt)
            user_ids = [row[0] for row in result]
            
            logger.info(f"Обработка активности за {target_date} для {len(user_ids)} пользователей")
            
            # Обновляем сводки для каждого пользователя
            for user_id in user_ids:
                await self.update_user_activity_summary(
                    user_id, ActivityPeriod.DAILY, target_date
                )
            
            # Если это воскресенье, обновляем еженедельные сводки
            if target_date.weekday() == 6:  # Воскресенье
                week_start = target_date - timedelta(days=6)
                for user_id in user_ids:
                    await self.update_user_activity_summary(
                        user_id, ActivityPeriod.WEEKLY, week_start
                    )
            
            logger.info(f"Обработка активности за {target_date} завершена")
            
        except Exception as e:
            logger.error(f"Ошибка обработки дневных активностей: {e}")
            raise ActivityException(f"Не удалось обработать активности: {e}")
    
    async def get_active_users_count_since(self, since: datetime) -> int:
        """Получение количества активных пользователей с указанной даты."""
        try:
            # Считаем пользователей, которые присоединились к группе с указанной даты
            stmt = select(func.count(User.id)).where(
                and_(
                    User.is_in_group == True,
                    User.joined_group_at >= since
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества активных пользователей: {e}")
            return 0
    
    async def get_activity_stats_for_date(self, target_date: date) -> Dict[str, Any]:
        """Получение статистики активности за дату."""
        try:
            # Количество сообщений за дату
            messages_stmt = select(func.count(ChatActivity.id)).where(
                func.date(ChatActivity.created_at) == target_date
            )
            messages_result = await self.session.execute(messages_stmt)
            messages_count = messages_result.scalar() or 0
            
            # Количество активных пользователей за дату
            users_stmt = select(func.count(func.distinct(UserActivity.user_id))).where(
                UserActivity.period_date == target_date
            )
            users_result = await self.session.execute(users_stmt)
            active_users = users_result.scalar() or 0
            
            return {
                'messages': messages_count,
                'active_users': active_users
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики активности за {target_date}: {e}")
            return {'messages': 0, 'active_users': 0}
    
    async def get_top_active_users(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение топ активных пользователей за период."""
        try:
            since_date = datetime.utcnow().date() - timedelta(days=days)
            
            stmt = (
                select(
                    ChatActivity.user_id,
                    User.first_name,
                    User.username,
                    func.count(ChatActivity.id).label('activity_count')
                )
                .join(User, ChatActivity.user_id == User.id)
                .where(ChatActivity.activity_date >= since_date)
                .group_by(ChatActivity.user_id, User.first_name, User.username)
                .order_by(func.count(ChatActivity.id).desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return [
                {
                    'user_id': row.user_id,
                    'first_name': row.first_name,
                    'username': row.username,
                    'activity_count': row.activity_count
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Ошибка получения топ активных пользователей: {e}")
            return []
    
    async def get_message_types_stats_for_date(self, target_date: date) -> Dict[str, int]:
        """Получить статистику по типам сообщений за дату."""
        try:
            result = await self.session.execute(
                select(
                    ChatActivity.activity_type,
                    func.count(ChatActivity.id).label('count')
                )
                .where(ChatActivity.activity_date == target_date)
                .group_by(ChatActivity.activity_type)
            )
            
            stats = {}
            for row in result:
                stats[row.activity_type] = row.count
            
            return stats
        except Exception as e:
            logger.error(f"Ошибка получения статистики типов сообщений за {target_date}: {e}")
            return {}
    
    async def get_message_types_stats_for_period(self, start_date: date, end_date: date) -> Dict[str, int]:
        """Получить статистику по типам сообщений за период."""
        try:
            result = await self.session.execute(
                select(
                    ChatActivity.activity_type,
                    func.count(ChatActivity.id).label('count')
                )
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
                .group_by(ChatActivity.activity_type)
            )
            
            stats = {}
            for row in result:
                stats[row.activity_type] = row.count
            
            return stats
        except Exception as e:
            logger.error(f"Ошибка получения статистики типов сообщений за период {start_date}-{end_date}: {e}")
            return {}
    
    async def get_activity_stats_for_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Получить общую статистику активности за период."""
        try:
            # Общее количество сообщений
            total_messages_result = await self.session.execute(
                select(func.count(ChatActivity.id))
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
            )
            total_messages = total_messages_result.scalar() or 0
            
            # Количество уникальных пользователей
            unique_users_result = await self.session.execute(
                select(func.count(func.distinct(ChatActivity.user_id)))
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
            )
            unique_users = unique_users_result.scalar() or 0
            
            return {
                'messages': total_messages,
                'active_users': unique_users
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики активности за период {start_date}-{end_date}: {e}")
            return {'messages': 0, 'active_users': 0}
    
    async def get_activity_stats_by_chat(self, start_date: date, end_date: date) -> Dict[str, Dict[str, Any]]:
        """Получить статистику активности по чатам за период."""
        try:
            chat_stats = {}
            
            # Получаем список всех чатов из базы
            chats_stmt = select(ChatActivity.chat_id).distinct()
            chats_result = await self.session.execute(chats_stmt)
            chat_ids = [row.chat_id for row in chats_result]
            
            for chat_id in chat_ids:
                # Общая статистика по чату
                stats_stmt = (
                    select(
                        func.count(ChatActivity.id).label('total_messages'),
                        func.count(func.distinct(ChatActivity.user_id)).label('unique_users')
                    )
                    .where(
                        and_(
                            ChatActivity.chat_id == chat_id,
                            ChatActivity.activity_date >= start_date,
                            ChatActivity.activity_date <= end_date
                        )
                    )
                )
                
                stats_result = await self.session.execute(stats_stmt)
                stats_row = stats_result.first()
                
                # Статистика по типам сообщений
                types_stmt = (
                    select(
                        ChatActivity.activity_type,
                        func.count(ChatActivity.id).label('count')
                    )
                    .where(
                        and_(
                            ChatActivity.chat_id == chat_id,
                            ChatActivity.activity_date >= start_date,
                            ChatActivity.activity_date <= end_date
                        )
                    )
                    .group_by(ChatActivity.activity_type)
                )
                
                types_result = await self.session.execute(types_stmt)
                message_types = {row.activity_type: row.count for row in types_result}
                
                # Топ пользователей в чате
                users_stmt = (
                    select(
                        ChatActivity.user_id,
                        User.first_name,
                        User.username,
                        func.count(ChatActivity.id).label('message_count')
                    )
                    .join(User, ChatActivity.user_id == User.id)
                    .where(
                        and_(
                            ChatActivity.chat_id == chat_id,
                            ChatActivity.activity_date >= start_date,
                            ChatActivity.activity_date <= end_date
                        )
                    )
                    .group_by(ChatActivity.user_id, User.first_name, User.username)
                    .order_by(func.count(ChatActivity.id).desc())
                    .limit(5)
                )
                
                users_result = await self.session.execute(users_stmt)
                top_users = [
                    {
                        'first_name': row.first_name,
                        'username': row.username,
                        'message_count': row.message_count
                    }
                    for row in users_result
                ]
                
                chat_stats[chat_id] = {
                    'total_messages': stats_row.total_messages,
                    'unique_users': stats_row.unique_users,
                    'message_types': message_types,
                    'top_users': top_users
                }
            
            return chat_stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики по чатам: {e}")
            return {}
    
    async def get_overall_activity_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Получить общую статистику активности по всем чатам."""
        try:
            # Общая статистика
            stats_stmt = (
                select(
                    func.count(ChatActivity.id).label('total_messages'),
                    func.count(func.distinct(ChatActivity.user_id)).label('unique_users'),
                    func.count(func.distinct(ChatActivity.chat_id)).label('active_chats')
                )
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
            )
            
            stats_result = await self.session.execute(stats_stmt)
            stats_row = stats_result.first()
            
            # Общая статистика по типам сообщений
            types_stmt = (
                select(
                    ChatActivity.activity_type,
                    func.count(ChatActivity.id).label('count')
                )
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
                .group_by(ChatActivity.activity_type)
            )
            
            types_result = await self.session.execute(types_stmt)
            message_types = {row.activity_type: row.count for row in types_result}
            
            # Общий топ пользователей
            users_stmt = (
                select(
                    ChatActivity.user_id,
                    User.first_name,
                    User.username,
                    func.count(ChatActivity.id).label('message_count')
                )
                .join(User, ChatActivity.user_id == User.id)
                .where(
                    and_(
                        ChatActivity.activity_date >= start_date,
                        ChatActivity.activity_date <= end_date
                    )
                )
                .group_by(ChatActivity.user_id, User.first_name, User.username)
                .order_by(func.count(ChatActivity.id).desc())
                .limit(10)
            )
            
            users_result = await self.session.execute(users_stmt)
            top_users = [
                {
                    'first_name': row.first_name,
                    'username': row.username,
                    'message_count': row.message_count
                }
                for row in users_result
            ]
            
            return {
                'total_messages': stats_row.total_messages,
                'unique_users': stats_row.unique_users,
                'active_chats': stats_row.active_chats,
                'message_types': message_types,
                'top_users': top_users
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения общей статистики: {e}")
            return {
                'total_messages': 0,
                'unique_users': 0,
                'active_chats': 0,
                'message_types': {},
                'top_users': []
            }
    
    async def get_top_active_users_for_chat(self, chat_id: str, days: int = 7, limit: int = 50) -> List[Dict]:
        """Получить топ активных пользователей для конкретного чата."""
        try:
            start_date = (datetime.utcnow() - timedelta(days=days)).date()
            
            stmt = (
                select(
                    ChatActivity.user_id,
                    User.first_name,
                    User.username,
                    func.count(ChatActivity.id).label('activity_count')
                )
                .join(User, ChatActivity.user_id == User.id)
                .where(
                    and_(
                        ChatActivity.chat_id == chat_id,
                        ChatActivity.activity_date >= start_date
                    )
                )
                .group_by(ChatActivity.user_id, User.first_name, User.username)
                .order_by(func.count(ChatActivity.id).desc())
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return [
                {
                    'first_name': row.first_name,
                    'username': row.username,
                    'activity_count': row.activity_count
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей для чата {chat_id}: {e}")
            return []

