"""
Сервис для управления участниками группы.

Отслеживает подписки и исключает неоплативших пользователей.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.database import get_db_session
from app.services.user_service import UserService
from app.services.telegram_service import TelegramService
from config.settings import get_settings


class GroupManagementService:
    """Сервис для управления участниками группы."""
    
    def __init__(self, bot=None):
        self.settings = get_settings()
        self.telegram_service = TelegramService(bot) if bot else None
    
    async def check_subscriptions_and_kick_unpaid(self) -> Dict[str, Any]:
        """
        Проверяет подписки всех участников группы и исключает неоплативших.
        
        Returns:
            Dict с результатами операции
        """
        try:
            logger.info("🔍 Начинаем проверку подписок участников группы...")
            
            async with get_db_session() as session:
                user_service = UserService(session)
                
                # Получаем всех пользователей в группе
                group_members = await user_service.get_users_in_group()
                logger.info(f"👥 Найдено {len(group_members)} участников в группе")
                
                results = {
                    "total_checked": len(group_members),
                    "warnings_sent": 0,
                    "warnings_failed": 0,
                    "kicked_users": 0,
                    "errors": 0,
                    "details": []
                }
                
                for i, user in enumerate(group_members, 1):
                    logger.info(f"🔄 Обрабатываем пользователя {i}/{len(group_members)}: {user.telegram_id} (@{user.username})")
                    try:
                        await self._process_user_subscription(user, user_service, results)
                    except Exception as e:
                        logger.error(f"Ошибка обработки пользователя {user.telegram_id}: {e}")
                        results["errors"] += 1
                        results["details"].append({
                            "user_id": user.telegram_id,
                            "action": "error",
                            "message": str(e)
                        })
                
                logger.info(f"✅ Проверка завершена: {results}")
                logger.info(f"🔄 Все задачи исключения запущены в фоне, система продолжает работать")
                return results
                
        except Exception as e:
            logger.error(f"Критическая ошибка при проверке подписок: {e}")
            return {
                "total_checked": 0,
                "warnings_sent": 0,
                "kicked_users": 0,
                "errors": 1,
                "details": [{"error": str(e)}]
            }
    
    async def _process_user_subscription(self, user, user_service: UserService, results: Dict[str, Any]) -> None:
        """Обрабатывает подписку конкретного пользователя."""
        
        logger.info(f"🔍 Проверяем пользователя {user.telegram_id} (@{user.username})")
        logger.info(f"   Статус: {user.status}, Premium: {user.is_premium}, Подписка до: {user.subscription_until}")
        
        # Проверяем, есть ли активная подписка
        has_active_subscription = (
            user.status == "active" and 
            user.is_premium and 
            user.subscription_until and 
            user.subscription_until > datetime.utcnow()
        )
        
        if has_active_subscription:
            logger.info(f"✅ Пользователь {user.telegram_id} (@{user.username}) имеет активную подписку")
            return
        
        # Если пользователь не оплатил, отправляем предупреждение
        logger.warning(f"⚠️ Пользователь {user.telegram_id} (@{user.username}) НЕ ОПЛАЧИВАЛ - отправляем предупреждение")
        
        warning_sent = await self._send_payment_warning(user)
        if warning_sent:
            results["warnings_sent"] += 1
            results["details"].append({
                "user_id": user.telegram_id,
                "action": "warning_sent",
                "username": user.username
            })
        else:
            results["warnings_failed"] += 1
            results["details"].append({
                "user_id": user.telegram_id,
                "action": "warning_failed",
                "username": user.username
            })
        
        # Планируем исключение через 30 минут (асинхронно)
        logger.info(f"⏰ Планируем исключение пользователя {user.telegram_id} через 30 минут")
        # Создаем задачу в фоне, чтобы не блокировать обработку других пользователей
        import asyncio
        asyncio.create_task(self._schedule_user_kick(user.telegram_id))
    
    async def _send_payment_warning(self, user) -> bool:
        """Отправляет предупреждение о необходимости оплаты."""
        try:
            warning_message = f"""⚠️ <b>ВНИМАНИЕ!</b>

Привет, {user.first_name}!

Твоя подписка на клуб «ОСНОВА ПУТИ» истекла или не была оплачена.

🕐 <b>У тебя есть 30 минут</b> чтобы:
• Оплатить подписку ($33)
• Или связаться с администратором для выдачи доступа

Если в течение 30 минут ты не оплатишь или не получишь доступ от администратора, тебя исключат из группы.

💳 <b>Для оплаты:</b>
1. Нажми /start в личных сообщениях с ботом
2. Выбери "Получить доступ - $33"
3. Оплати любым удобным способом

📞 <b>Для связи с администратором:</b>
Напиши в личные сообщения боту - администратор ответит в течение 30 минут.

⏰ <b>Осталось времени:</b> 30 минут

Не теряй доступ к сообществу! 🚀"""

            # Отправляем сообщение в личные сообщения
            sent = await self.telegram_service.send_message(
                user.telegram_id,
                warning_message,
                parse_mode='HTML'
            )
            
            if sent:
                logger.info(f"📤 Предупреждение отправлено пользователю {user.telegram_id} (@{user.username})")
                return True
            else:
                logger.warning(f"❌ Не удалось отправить предупреждение пользователю {user.telegram_id} (@{user.username}) - возможно, пользователь не начинал диалог с ботом")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка отправки предупреждения пользователю {user.telegram_id}: {e}")
            return False
    
    async def _schedule_user_kick(self, telegram_id: int) -> None:
        """Планирует исключение пользователя через 30 минут."""
        try:
            logger.info(f"⏳ Запущена задача исключения для пользователя {telegram_id} - ожидание 30 минут...")
            # Ждем 30 минут
            await asyncio.sleep(30 * 60)  # 30 минут в секундах
            logger.info(f"⏰ Время ожидания истекло для пользователя {telegram_id} - проверяем оплату...")
            
            # Проверяем, оплатил ли пользователь за это время
            await self._kick_user_if_unpaid(telegram_id)
            
        except Exception as e:
            logger.error(f"Ошибка при планировании исключения пользователя {telegram_id}: {e}")
    
    async def _kick_user_if_unpaid(self, telegram_id: int) -> None:
        """Исключает пользователя, если он не оплатил."""
        try:
            async with get_db_session() as session:
                user_service = UserService(session)
                
                # Получаем актуальную информацию о пользователе
                user = await user_service.get_user_by_telegram_id(telegram_id)
                
                if not user:
                    logger.warning(f"Пользователь {telegram_id} не найден в базе данных")
                    return
                
                # Проверяем, оплатил ли пользователь за это время
                has_active_subscription = (
                    user.status == "active" and 
                    user.is_premium and 
                    user.subscription_until and 
                    user.subscription_until > datetime.utcnow()
                )
                
                if has_active_subscription:
                    logger.info(f"✅ Пользователь {telegram_id} оплатил подписку, исключение отменено")
                    return
                
                # Исключаем пользователя из группы
                await self._kick_user_from_group(telegram_id)
                
                # Обновляем статус в базе данных
                from app.schemas.user import UserUpdate
                await user_service.update_user(str(user.id), UserUpdate(
                    is_in_group=False,
                    status="pending"
                ))
                
                logger.info(f"🚫 Пользователь {telegram_id} исключен из группы")
                
        except Exception as e:
            logger.error(f"Ошибка при исключении пользователя {telegram_id}: {e}")
    
    async def _kick_user_from_group(self, telegram_id: int) -> None:
        """Исключает пользователя из группы."""
        try:
            # Исключаем пользователя из группы
            success = await self.telegram_service.kick_chat_member(
                chat_id=int(self.settings.GROUP_ID),
                user_id=telegram_id
            )
            
            if success:
                logger.info(f"✅ Пользователь {telegram_id} успешно исключен из группы")
            else:
                logger.warning(f"❌ Не удалось исключить пользователя {telegram_id} из группы")
                
        except Exception as e:
            logger.error(f"Ошибка исключения пользователя {telegram_id} из группы: {e}")
    
    async def add_user_to_group(self, telegram_id: int) -> bool:
        """
        Добавляет пользователя обратно в группу.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            bool: True если пользователь добавлен успешно
        """
        try:
            success = await self.telegram_service.unban_chat_member(
                chat_id=int(self.settings.GROUP_ID),
                user_id=telegram_id
            )
            
            if success:
                logger.info(f"✅ Пользователь {telegram_id} добавлен обратно в группу")
                
                # Обновляем статус в базе данных
                async with get_db_session() as session:
                    user_service = UserService(session)
                    user = await user_service.get_user_by_telegram_id(telegram_id)
                    
                    if user:
                        from app.schemas.user import UserUpdate
                        await user_service.update_user(str(user.id), UserUpdate(
                            is_in_group=True,
                            joined_group_at=datetime.utcnow()
                        ))
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {telegram_id} в группу: {e}")
            return False
