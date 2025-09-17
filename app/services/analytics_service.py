"""
Сервис аналитики для ClubBot согласно ТЗ.

Анализирует активность участников и формирует еженедельные отчеты.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.report import Report
from app.models.goal import Goal
from app.models.activity import UserActivity


class AnalyticsService:
    """Сервис для анализа активности участников."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация сервиса."""
        self.session = session
    
    async def get_weekly_activity_stats(self, start_date: datetime = None) -> Dict[str, Any]:
        """
        Получение статистики активности за неделю согласно ТЗ.
        
        Args:
            start_date: Начальная дата недели (по умолчанию - неделю назад)
            
        Returns:
            Dict: Статистика активности
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            
            end_date = start_date + timedelta(days=7)
            
            # Получаем всех активных пользователей
            active_users_query = select(User).where(
                and_(
                    User.is_premium == True,
                    User.subscription_end > datetime.utcnow()
                )
            )
            active_users_result = await self.session.execute(active_users_query)
            active_users = active_users_result.scalars().all()
            
            user_stats = []
            
            for user in active_users:
                # Считаем отчеты за неделю
                reports_query = select(func.count(Report.id)).where(
                    and_(
                        Report.user_id == user.id,
                        Report.created_at >= start_date,
                        Report.created_at <= end_date
                    )
                )
                reports_result = await self.session.execute(reports_query)
                reports_count = reports_result.scalar() or 0
                
                # Считаем цели за неделю
                goals_query = select(func.count(Goal.id)).where(
                    and_(
                        Goal.user_id == user.id,
                        Goal.created_at >= start_date,
                        Goal.created_at <= end_date
                    )
                )
                goals_result = await self.session.execute(goals_query)
                goals_count = goals_result.scalar() or 0
                
                # Считаем общую активность
                activity_score = reports_count * 2 + goals_count * 3  # Веса для разных типов активности
                
                user_stats.append({
                    'user_id': user.id,
                    'telegram_id': user.telegram_id,
                    'username': user.username or f"user_{user.telegram_id}",
                    'reports_count': reports_count,
                    'goals_count': goals_count,
                    'activity_score': activity_score
                })
            
            # Сортируем по активности
            user_stats.sort(key=lambda x: x['activity_score'], reverse=True)
            
            # Определяем топ активных (первые 3)
            top_active = []
            connecting = []
            
            for i, user_stat in enumerate(user_stats):
                if i < 3 and user_stat['activity_score'] > 0:
                    top_active.append(user_stat['username'])
                elif user_stat['activity_score'] == 0 or (i >= 3 and user_stat['activity_score'] < 5):
                    connecting.append(user_stat['username'])
            
            # Формируем итоговую статистику
            stats = {
                'period_start': start_date,
                'period_end': end_date,
                'total_users': len(active_users),
                'active_users': len([u for u in user_stats if u['activity_score'] > 0]),
                'inactive_users': len([u for u in user_stats if u['activity_score'] == 0]),
                'top_active': top_active[:3],  # Максимум 3 пользователя
                'connecting': connecting[:3],  # Максимум 3 пользователя
                'user_stats': user_stats,
                'total_reports': sum(u['reports_count'] for u in user_stats),
                'total_goals': sum(u['goals_count'] for u in user_stats),
                'average_activity': sum(u['activity_score'] for u in user_stats) / len(user_stats) if user_stats else 0
            }
            
            logger.info(f"Сформирована статистика активности: {stats['active_users']}/{stats['total_users']} активных")
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики активности: {e}")
            return {
                'period_start': start_date or datetime.utcnow() - timedelta(days=7),
                'period_end': (start_date or datetime.utcnow() - timedelta(days=7)) + timedelta(days=7),
                'total_users': 0,
                'active_users': 0,
                'inactive_users': 0,
                'top_active': [],
                'connecting': [],
                'user_stats': [],
                'total_reports': 0,
                'total_goals': 0,
                'average_activity': 0
            }
    
    async def get_admin_activity_report(self, start_date: datetime = None) -> str:
        """
        Формирование детального отчета для админа согласно ТЗ.
        
        Args:
            start_date: Начальная дата недели
            
        Returns:
            str: Форматированный отчет для админа
        """
        try:
            stats = await self.get_weekly_activity_stats(start_date)
            
            report = f"""
📊 <b>Еженедельный отчет активности</b>

<b>Период:</b> {stats['period_start'].strftime('%d.%m.%Y')} - {stats['period_end'].strftime('%d.%m.%Y')}

<b>Общая статистика:</b>
👥 Всего участников: {stats['total_users']}
✅ Активных: {stats['active_users']}
❌ Неактивных: {stats['inactive_users']}
📝 Всего отчетов: {stats['total_reports']}
🎯 Всего целей: {stats['total_goals']}
📈 Средняя активность: {stats['average_activity']:.1f}

<b>Топ включённых:</b>
"""
            
            if stats['top_active']:
                for i, username in enumerate(stats['top_active'], 1):
                    report += f"{i}. @{username}\n"
            else:
                report += "Нет активных участников\n"
            
            report += "\n<b>Подключаемся:</b>\n"
            if stats['connecting']:
                for username in stats['connecting']:
                    report += f"• @{username}\n"
            else:
                report += "Все участники активны!\n"
            
            # Детальная статистика по пользователям
            report += "\n<b>Детальная статистика:</b>\n"
            for user_stat in stats['user_stats'][:10]:  # Показываем топ-10
                report += f"@{user_stat['username']}: {user_stat['reports_count']} отчетов, {user_stat['goals_count']} целей (баллы: {user_stat['activity_score']})\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка формирования отчета для админа: {e}")
            return "❌ Ошибка формирования отчета"
    
    async def get_public_activity_message(self, start_date: datetime = None) -> str:
        """
        Формирование публичного сообщения для группы согласно ТЗ.
        
        Args:
            start_date: Начальная дата недели
            
        Returns:
            str: Форматированное сообщение для группы
        """
        try:
            stats = await self.get_weekly_activity_stats(start_date)
            
            # Формируем список топ активных
            top_active_str = ", ".join([f"@{username}" for username in stats['top_active']]) if stats['top_active'] else "Пока нет лидеров"
            
            # Формируем список подключающихся
            connecting_str = ", ".join([f"@{username}" for username in stats['connecting']]) if stats['connecting'] else "Все на высоте!"
            
            message = f"""
📊 <b>Еженедельный анализ активности</b>

<b>Топ включённых:</b> {top_active_str}
<b>Подключаемся:</b> {connecting_str}

Продолжаем держать ритм! 💪
"""
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка формирования публичного сообщения: {e}")
            return """
📊 <b>Еженедельный анализ активности</b>

<b>Топ включённых:</b> Данные обновляются...
<b>Подключаемся:</b> Данные обновляются...

Продолжаем держать ритм! 💪
"""
    
    async def update_user_activity(self, user_id: int, activity_type: str, details: str = "") -> bool:
        """
        Обновление активности пользователя.
        
        Args:
            user_id: ID пользователя
            activity_type: Тип активности (report, goal, ritual, etc.)
            details: Дополнительные детали
            
        Returns:
            bool: True если успешно
        """
        try:
            # Находим пользователя
            user_query = select(User).where(User.telegram_id == user_id)
            user_result = await self.session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Пользователь {user_id} не найден для обновления активности")
                return False
            
            # Создаем запись об активности
            activity = UserActivity(
                user_id=user.id,
                activity_type=activity_type,
                details=details,
                created_at=datetime.utcnow()
            )
            
            self.session.add(activity)
            await self.session.commit()
            
            logger.info(f"Обновлена активность пользователя {user_id}: {activity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления активности пользователя {user_id}: {e}")
            await self.session.rollback()
            return False
    
    async def get_user_weekly_summary(self, user_id: int, start_date: datetime = None) -> Dict[str, Any]:
        """
        Получение недельной сводки для пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            start_date: Начальная дата недели
            
        Returns:
            Dict: Сводка активности пользователя
        """
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            
            end_date = start_date + timedelta(days=7)
            
            # Находим пользователя
            user_query = select(User).where(User.telegram_id == user_id)
            user_result = await self.session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {'error': 'Пользователь не найден'}
            
            # Считаем отчеты
            reports_query = select(func.count(Report.id)).where(
                and_(
                    Report.user_id == user.id,
                    Report.created_at >= start_date,
                    Report.created_at <= end_date
                )
            )
            reports_result = await self.session.execute(reports_query)
            reports_count = reports_result.scalar() or 0
            
            # Считаем цели
            goals_query = select(func.count(Goal.id)).where(
                and_(
                    Goal.user_id == user.id,
                    Goal.created_at >= start_date,
                    Goal.created_at <= end_date
                )
            )
            goals_result = await self.session.execute(goals_query)
            goals_count = goals_result.scalar() or 0
            
            return {
                'user_id': user_id,
                'username': user.username,
                'reports_count': reports_count,
                'goals_count': goals_count,
                'activity_score': reports_count * 2 + goals_count * 3,
                'period_start': start_date,
                'period_end': end_date
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сводки пользователя {user_id}: {e}")
            return {'error': str(e)}
