"""
Сервис для работы с напоминаниями.

Содержит методы для управления напоминаниями пользователей.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.payment import Payment, PaymentStatus


class ReminderService:
    """Сервис для работы с напоминаниями."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация сервиса."""
        self.session = session
    
    async def get_users_needing_reminder(self, days_before: int = 3) -> List[User]:
        """Получение пользователей, которым нужно отправить напоминание."""
        try:
            # Вычисляем дату, когда нужно отправить напоминание
            reminder_date = datetime.now() + timedelta(days=days_before)
            
            # Находим пользователей с активными подписками, которые заканчиваются в указанную дату
            stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end <= reminder_date,
                    Payment.subscription_end > datetime.now(),
                    User.is_active == True
                )
            )
            
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            logger.info(f"Найдено {len(users)} пользователей для напоминания о продлении")
            return users
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей для напоминания: {e}")
            return []
    
    async def get_reminder_message(self, user: User, days_left: int) -> str:
        """Получение текста напоминания для пользователя."""
        if days_left == 1:
            message = f"""
⏰ <b>Напоминание о продлении</b>

Привет, {user.first_name}! 👋

Твоя подписка заканчивается <b>завтра</b>.

Чтобы не потерять доступ к клубу, продли подписку сейчас.

🎯 <b>Преимущества продления:</b>
• Продолжение ритуалов ЯДРА
• Доступ к закрытому чату
• Еженедельные отчеты
• Персональная поддержка

Продлить подписку?
"""
        elif days_left <= 3:
            message = f"""
⏰ <b>Напоминание о продлении</b>

Привет, {user.first_name}! 👋

Твоя подписка заканчивается через <b>{days_left} дня</b>.

Чтобы не потерять доступ к клубу, продли подписку сейчас.

🎯 <b>Преимущества продления:</b>
• Продолжение ритуалов ЯДРА
• Доступ к закрытому чату
• Еженедельные отчеты
• Персональная поддержка

Продлить подписку?
"""
        else:
            message = f"""
⏰ <b>Напоминание о продлении</b>

Привет, {user.first_name}! 👋

Твоя подписка заканчивается через <b>{days_left} дней</b>.

Чтобы не потерять доступ к клубу, продли подписку сейчас.

🎯 <b>Преимущества продления:</b>
• Продолжение ритуалов ЯДРА
• Доступ к закрытому чату
• Еженедельные отчеты
• Персональная поддержка

Продлить подписку?
"""
        
        return message
    
    async def get_enabled_reminders_count(self) -> int:
        """Получение количества активных напоминаний."""
        try:
            # Считаем пользователей с активными подписками
            stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end > datetime.now(),
                    User.is_active == True
                )
            )
            
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            return len(users)
            
        except Exception as e:
            logger.error(f"Ошибка подсчета активных напоминаний: {e}")
            return 0
    
    async def get_expired_subscriptions(self) -> List[User]:
        """Получение пользователей с истекшими подписками."""
        try:
            stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end < datetime.now(),
                    User.is_active == True
                )
            )
            
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            logger.info(f"Найдено {len(users)} пользователей с истекшими подписками")
            return users
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователей с истекшими подписками: {e}")
            return []
    
    async def deactivate_expired_users(self) -> int:
        """Деактивация пользователей с истекшими подписками."""
        try:
            expired_users = await self.get_expired_subscriptions()
            
            for user in expired_users:
                user.is_active = False
                user.updated_at = datetime.now()
                logger.info(f"Деактивирован пользователь {user.telegram_id} (истекла подписка)")
            
            await self.session.commit()
            logger.info(f"Деактивировано {len(expired_users)} пользователей")
            return len(expired_users)
            
        except Exception as e:
            logger.error(f"Ошибка деактивации пользователей: {e}")
            await self.session.rollback()
            return 0
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """Получение статистики подписок."""
        try:
            # Активные подписки
            active_stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end > datetime.now(),
                    User.is_active == True
                )
            )
            active_result = await self.session.execute(active_stmt)
            active_users = active_result.scalars().all()
            
            # Истекающие в течение недели
            week_later = datetime.now() + timedelta(days=7)
            expiring_stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end <= week_later,
                    Payment.subscription_end > datetime.now(),
                    User.is_active == True
                )
            )
            expiring_result = await self.session.execute(expiring_stmt)
            expiring_users = expiring_result.scalars().all()
            
            # Истекшие подписки
            expired_stmt = select(User).join(Payment).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    Payment.subscription_end < datetime.now(),
                    User.is_active == True
                )
            )
            expired_result = await self.session.execute(expired_stmt)
            expired_users = expired_result.scalars().all()
            
            return {
                "active_subscriptions": len(active_users),
                "expiring_soon": len(expiring_users),
                "expired": len(expired_users),
                "total_users": len(active_users) + len(expired_users)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики подписок: {e}")
            return {
                "active_subscriptions": 0,
                "expiring_soon": 0,
                "expired": 0,
                "total_users": 0
            }
    
    async def send_renewal_reminder(self, user: User, days_left: int) -> bool:
        """Отправка напоминания о продлении подписки."""
        try:
            message = await self.get_reminder_message(user, days_left)
            
            # Здесь должна быть отправка сообщения через TelegramService
            # Пока возвращаем True как заглушку
            logger.info(f"Отправлено напоминание пользователю {user.telegram_id} ({days_left} дней до истечения)")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
            return False




