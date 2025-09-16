"""
Сервис для работы с отчетами пользователей.

Содержит логику создания, обновления и анализа отчетов.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.models import Report, ReportStatus, User
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:
    """Сервис для работы с отчетами."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.
        
        Args:
            session: Асинхронная сессия базы данных
        """
        self.session = session
    
    async def create_report_request(self, user_id: str, report_date: datetime) -> Report:
        """
        Создание запроса на отчет.
        
        Args:
            user_id: ID пользователя
            report_date: Дата отчета
            
        Returns:
            Report: Созданный отчет
        """
        try:
            # Проверяем, нет ли уже отчета на эту дату
            existing_report = await self.get_report_by_date(user_id, report_date)
            if existing_report:
                return existing_report
            
            report = Report(
                user_id=user_id,
                report_date=report_date,
                status=ReportStatus.PENDING,
                requested_at=datetime.now()
            )
            
            self.session.add(report)
            await self.session.commit()
            await self.session.refresh(report)
            
            logger.info(f"Создан запрос на отчет для пользователя {user_id} на дату {report_date.date()}")
            return report
            
        except Exception as e:
            logger.error(f"Ошибка создания запроса на отчет: {e}")
            await self.session.rollback()
            raise
    
    async def submit_report(self, user_id: str, report_date: datetime, text: str) -> Report:
        """
        Отправка отчета пользователем.
        
        Args:
            user_id: ID пользователя
            report_date: Дата отчета
            text: Текст отчета
            
        Returns:
            Report: Обновленный отчет
        """
        try:
            report = await self.get_report_by_date(user_id, report_date)
            if not report:
                # Создаем новый отчет если не существует
                report = await self.create_report_request(user_id, report_date)
            
            report.text = text
            report.status = ReportStatus.SENT
            report.submitted_at = datetime.now()
            
            await self.session.commit()
            await self.session.refresh(report)
            
            logger.info(f"Получен отчет от пользователя {user_id} на дату {report_date.date()}")
            return report
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
            await self.session.rollback()
            raise
    
    async def skip_report(self, user_id: str, report_date: datetime) -> Report:
        """
        Пропуск отчета пользователем.
        
        Args:
            user_id: ID пользователя
            report_date: Дата отчета
            
        Returns:
            Report: Обновленный отчет
        """
        try:
            report = await self.get_report_by_date(user_id, report_date)
            if not report:
                # Создаем новый отчет если не существует
                report = await self.create_report_request(user_id, report_date)
            
            report.status = ReportStatus.SKIPPED
            report.submitted_at = datetime.now()
            
            await self.session.commit()
            await self.session.refresh(report)
            
            logger.info(f"Пользователь {user_id} пропустил отчет на дату {report_date.date()}")
            return report
            
        except Exception as e:
            logger.error(f"Ошибка пропуска отчета: {e}")
            await self.session.rollback()
            raise
    
    async def get_report_by_date(self, user_id: str, report_date: datetime) -> Optional[Report]:
        """
        Получение отчета по дате.
        
        Args:
            user_id: ID пользователя
            report_date: Дата отчета
            
        Returns:
            Optional[Report]: Отчет или None
        """
        try:
            # Получаем дату без времени для сравнения
            date_only = report_date.date()
            
            stmt = select(Report).where(
                and_(
                    Report.user_id == user_id,
                    func.date(Report.report_date) == date_only
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета по дате: {e}")
            return None
    
    async def get_user_reports_for_week(self, user_id: str, start_date: datetime) -> List[Report]:
        """
        Получение отчетов пользователя за неделю.
        
        Args:
            user_id: ID пользователя
            start_date: Начало недели
            
        Returns:
            List[Report]: Список отчетов
        """
        try:
            end_date = start_date + timedelta(days=7)
            
            stmt = select(Report).where(
                and_(
                    Report.user_id == user_id,
                    Report.report_date >= start_date,
                    Report.report_date < end_date
                )
            ).order_by(Report.report_date)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка получения отчетов за неделю: {e}")
            return []
    
    async def get_weekly_activity_stats(self, start_date: datetime) -> Dict[str, Any]:
        """
        Получение статистики активности за неделю.
        
        Args:
            start_date: Начало недели
            
        Returns:
            Dict[str, Any]: Статистика активности
        """
        try:
            end_date = start_date + timedelta(days=7)
            
            # Получаем количество отчетов по пользователям
            stmt = select(
                Report.user_id,
                User.username,
                User.first_name,
                func.count(Report.id).label('report_count')
            ).join(User).where(
                and_(
                    Report.report_date >= start_date,
                    Report.report_date < end_date,
                    Report.status == ReportStatus.SENT
                )
            ).group_by(Report.user_id, User.username, User.first_name)
            
            result = await self.session.execute(stmt)
            user_stats = result.all()
            
            # Разделяем на активных и неактивных
            active_users = []
            inactive_users = []
            
            for user_stat in user_stats:
                user_info = {
                    'user_id': user_stat.user_id,
                    'username': user_stat.username,
                    'first_name': user_stat.first_name,
                    'report_count': user_stat.report_count
                }
                
                if user_stat.report_count >= 4:  # 4+ отчета = активный
                    active_users.append(user_info)
                elif user_stat.report_count < 2:  # < 2 отчетов = неактивный
                    inactive_users.append(user_info)
            
            return {
                'week_start': start_date,
                'week_end': end_date,
                'active_users': active_users,
                'inactive_users': inactive_users,
                'total_reports': sum(stat.report_count for stat in user_stats)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики активности: {e}")
            return {
                'week_start': start_date,
                'week_end': start_date + timedelta(days=7),
                'active_users': [],
                'inactive_users': [],
                'total_reports': 0
            }
    
    async def mark_missed_reports(self, cutoff_date: datetime) -> int:
        """
        Отметка пропущенных отчетов.
        
        Args:
            cutoff_date: Дата, до которой считать отчеты пропущенными
            
        Returns:
            int: Количество отмеченных как пропущенные
        """
        try:
            stmt = select(Report).where(
                and_(
                    Report.status == ReportStatus.PENDING,
                    Report.report_date < cutoff_date
                )
            )
            
            result = await self.session.execute(stmt)
            pending_reports = result.scalars().all()
            
            count = 0
            for report in pending_reports:
                report.status = ReportStatus.MISSED
                count += 1
            
            await self.session.commit()
            
            if count > 0:
                logger.info(f"Отмечено {count} отчетов как пропущенные")
            
            return count
            
        except Exception as e:
            logger.error(f"Ошибка отметки пропущенных отчетов: {e}")
            await self.session.rollback()
            return 0
    
    async def get_users_for_report_reminder(self, target_hour: int = None, target_minute: int = None) -> List[User]:
        """
        Получение списка пользователей для напоминания об отчете.
        
        Args:
            target_hour: Час для фильтрации (если None, возвращает всех)
            target_minute: Минута для фильтрации (если None, возвращает всех)
            
        Returns:
            List[User]: Список пользователей с активной подпиской
        """
        try:
            today = datetime.now().date()
            
            # Базовые условия
            conditions = [
                User.status == "active",
                or_(
                    User.subscription_until.is_(None),
                    func.date(User.subscription_until) > today
                )
            ]
            
            # Добавляем фильтр по времени, если указано
            if target_hour is not None and target_minute is not None:
                conditions.extend([
                    User.reminder_enabled == True,
                    User.reminder_time_hour == target_hour,
                    User.reminder_time_minute == target_minute
                ])
            
            stmt = select(User).where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей для напоминания: {e}")
            return []
