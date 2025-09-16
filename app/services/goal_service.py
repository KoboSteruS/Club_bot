"""
Сервис для работы с целями пользователей.

Содержит логику создания, обновления и управления еженедельными целями.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from loguru import logger

from app.models import Goal, GoalStatus, User


class GoalService:
    """Сервис для работы с целями."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса.
        
        Args:
            session: Асинхронная сессия базы данных
        """
        self.session = session
    
    def get_week_number_and_year(self, date: datetime) -> tuple[int, int]:
        """
        Получение номера недели и года.
        
        Args:
            date: Дата
            
        Returns:
            tuple[int, int]: Номер недели и год
        """
        # Используем ISO неделю (понедельник - первый день недели)
        year, week, _ = date.isocalendar()
        return week, year
    
    async def create_goal_request(self, user_id: str, date: datetime) -> Goal:
        """
        Создание запроса на постановку цели.
        
        Args:
            user_id: ID пользователя
            date: Дата для определения недели
            
        Returns:
            Goal: Созданная цель
        """
        try:
            week_number, year = self.get_week_number_and_year(date)
            
            # Проверяем, нет ли уже цели на эту неделю
            existing_goal = await self.get_goal_by_week(user_id, week_number, year)
            if existing_goal:
                return existing_goal
            
            goal = Goal(
                user_id=user_id,
                week_number=week_number,
                year=year,
                status=GoalStatus.PENDING
            )
            
            self.session.add(goal)
            await self.session.commit()
            await self.session.refresh(goal)
            
            logger.info(f"Создан запрос на цель для пользователя {user_id} на неделю {week_number}/{year}")
            return goal
            
        except Exception as e:
            logger.error(f"Ошибка создания запроса на цель: {e}")
            await self.session.rollback()
            raise
    
    async def set_goal(self, user_id: str, date: datetime, goal_text: str) -> Goal:
        """
        Установка цели пользователем.
        
        Args:
            user_id: ID пользователя
            date: Дата для определения недели
            goal_text: Текст цели
            
        Returns:
            Goal: Обновленная цель
        """
        try:
            week_number, year = self.get_week_number_and_year(date)
            
            goal = await self.get_goal_by_week(user_id, week_number, year)
            if not goal:
                # Создаем новую цель если не существует
                goal = await self.create_goal_request(user_id, date)
            
            goal.goal_text = goal_text
            goal.status = GoalStatus.ACTIVE
            goal.created_at = datetime.now()
            
            await self.session.commit()
            await self.session.refresh(goal)
            
            logger.info(f"Установлена цель для пользователя {user_id} на неделю {week_number}/{year}")
            return goal
            
        except Exception as e:
            logger.error(f"Ошибка установки цели: {e}")
            await self.session.rollback()
            raise
    
    async def complete_goal(self, user_id: str, date: datetime) -> Optional[Goal]:
        """
        Завершение цели.
        
        Args:
            user_id: ID пользователя
            date: Дата для определения недели
            
        Returns:
            Optional[Goal]: Завершенная цель или None
        """
        try:
            week_number, year = self.get_week_number_and_year(date)
            
            goal = await self.get_goal_by_week(user_id, week_number, year)
            if not goal or goal.status != GoalStatus.ACTIVE:
                return None
            
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.now()
            
            await self.session.commit()
            await self.session.refresh(goal)
            
            logger.info(f"Завершена цель для пользователя {user_id} на неделю {week_number}/{year}")
            return goal
            
        except Exception as e:
            logger.error(f"Ошибка завершения цели: {e}")
            await self.session.rollback()
            return None
    
    async def get_goal_by_week(self, user_id: str, week_number: int, year: int) -> Optional[Goal]:
        """
        Получение цели по номеру недели.
        
        Args:
            user_id: ID пользователя
            week_number: Номер недели
            year: Год
            
        Returns:
            Optional[Goal]: Цель или None
        """
        try:
            stmt = select(Goal).where(
                and_(
                    Goal.user_id == user_id,
                    Goal.week_number == week_number,
                    Goal.year == year
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Ошибка получения цели по неделе: {e}")
            return None
    
    async def get_current_goal(self, user_id: str) -> Optional[Goal]:
        """
        Получение текущей цели пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Goal]: Текущая цель или None
        """
        week_number, year = self.get_week_number_and_year(datetime.now())
        return await self.get_goal_by_week(user_id, week_number, year)
    
    async def get_user_goals(self, user_id: str, limit: int = 10) -> List[Goal]:
        """
        Получение целей пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество целей
            
        Returns:
            List[Goal]: Список целей
        """
        try:
            stmt = select(Goal).where(
                Goal.user_id == user_id
            ).order_by(Goal.year.desc(), Goal.week_number.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка получения целей пользователя: {e}")
            return []
    
    async def get_users_for_goal_reminder(self) -> List[User]:
        """
        Получение списка пользователей для напоминания о постановке цели.
        
        Returns:
            List[User]: Список пользователей с активной подпиской
        """
        try:
            today = datetime.now().date()
            
            stmt = select(User).where(
                and_(
                    User.status == "active",
                    or_(
                        User.subscription_until.is_(None),
                        func.date(User.subscription_until) > today
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей для напоминания о цели: {e}")
            return []
    
    async def archive_old_goals(self, weeks_ago: int = 12) -> int:
        """
        Архивирование старых целей.
        
        Args:
            weeks_ago: Количество недель назад для архивирования
            
        Returns:
            int: Количество архивированных целей
        """
        try:
            cutoff_date = datetime.now() - timedelta(weeks=weeks_ago)
            cutoff_week, cutoff_year = self.get_week_number_and_year(cutoff_date)
            
            # Находим старые завершенные или отмененные цели
            stmt = select(Goal).where(
                and_(
                    Goal.status.in_([GoalStatus.COMPLETED, GoalStatus.CANCELLED]),
                    or_(
                        Goal.year < cutoff_year,
                        and_(
                            Goal.year == cutoff_year,
                            Goal.week_number < cutoff_week
                        )
                    )
                )
            )
            
            result = await self.session.execute(stmt)
            old_goals = result.scalars().all()
            
            # Помечаем их как архивированные (или удаляем, если нужно)
            count = 0
            for goal in old_goals:
                # В данном случае просто удаляем старые цели
                # Можно изменить на статус "archived" если нужно сохранять
                await self.session.delete(goal)
                count += 1
            
            await self.session.commit()
            
            if count > 0:
                logger.info(f"Архивировано {count} старых целей")
            
            return count
            
        except Exception as e:
            logger.error(f"Ошибка архивирования старых целей: {e}")
            await self.session.rollback()
            return 0
