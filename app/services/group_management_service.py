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
                
                # ВАЖНО: Отключаем синхронизацию, так как Telegram API не позволяет получить полный список участников
                # Вместо этого проверяем всех пользователей в базе, которые могут быть в группе
                logger.info("⚠️ Синхронизация отключена - Telegram API не позволяет получить полный список участников")
                
                # Получаем всех пользователей в группе (по базе данных)
                group_members = await user_service.get_users_in_group()
                logger.info(f"👥 Найдено {len(group_members)} участников в группе (по базе данных)")
                
                # Дополнительно получаем всех пользователей для проверки
                all_users = await user_service.get_all_users()
                logger.info(f"📊 Всего пользователей в базе: {len(all_users)}")
                
                # Проверяем всех пользователей, которые могут быть в группе
                # (статус active или pending, независимо от is_in_group)
                potential_group_members = [user for user in all_users if user.status in ['active', 'pending']]
                logger.info(f"🔍 Потенциальных участников группы: {len(potential_group_members)}")
                
                # Используем потенциальных участников для проверки
                if len(potential_group_members) > len(group_members):
                    logger.info(f"⚠️ Обнаружено больше потенциальных участников ({len(potential_group_members)}) чем в группе ({len(group_members)})")
                    logger.info("🔄 Проверяем всех потенциальных участников...")
                    group_members = potential_group_members
                
                results = {
                    "total_checked": len(group_members),
                    "warnings_sent": 0,
                    "warnings_failed": 0,
                    "kicked_users": 0,
                    "errors": 0,
                    "details": []
                }
                
                # Логируем список пользователей для проверки
                logger.info("📋 Список пользователей для проверки:")
                for i, user in enumerate(group_members, 1):
                    logger.info(f"  {i}. {user.telegram_id} (@{user.username}) - Статус: {user.status}, Premium: {user.is_premium}, В группе: {user.is_in_group}")
                
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
        
        # ВАЖНО: Проверяем, действительно ли пользователь в группе
        if not user.is_in_group:
            logger.info(f"ℹ️ Пользователь {user.telegram_id} (@{user.username}) не в группе (is_in_group=False), пропускаем")
            return
        
        # Дополнительная проверка через Telegram API
        try:
            if self.telegram_service and self.telegram_service.bot:
                chat_member = await self.telegram_service.bot.get_chat_member(
                    chat_id=int(self.settings.GROUP_ID),
                    user_id=user.telegram_id
                )
                
                if chat_member.status in ['left', 'kicked']:
                    logger.info(f"ℹ️ Пользователь {user.telegram_id} (@{user.username}) покинул группу (статус: {chat_member.status}), обновляем базу и пропускаем")
                    
                    # Обновляем статус в базе данных
                    user.is_in_group = False
                    user.joined_group_at = None
                    await user_service.session.commit()
                    return
                    
        except Exception as e:
            logger.warning(f"⚠️ Не удалось проверить статус пользователя {user.telegram_id} в группе: {e}")
            # Продолжаем обработку, если не можем проверить через API
        
        # Проверяем, отправляли ли уже предупреждение сегодня
        today = datetime.utcnow().date()
        last_warning_date = user.last_subscription_check.date() if user.last_subscription_check else None
        
        if last_warning_date == today:
            logger.info(f"ℹ️ Пользователю {user.telegram_id} (@{user.username}) уже отправляли предупреждение сегодня, пропускаем")
            return
        
        # Если пользователь не оплатил, отправляем предупреждение
        logger.warning(f"⚠️ Пользователь {user.telegram_id} (@{user.username}) НЕ ОПЛАЧИВАЛ - отправляем предупреждение")
        
        warning_sent = await self._send_payment_warning(user)
        if warning_sent:
            # Обновляем дату последнего предупреждения
            user.last_subscription_check = datetime.utcnow()
            await user_service.session.commit()
            
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
        
        # Планируем исключение через 3 дня (асинхронно)
        logger.info(f"⏰ Планируем исключение пользователя {user.telegram_id} через 3 дня")
        # Создаем задачу в фоне, чтобы не блокировать обработку других пользователей
        import asyncio
        asyncio.create_task(self._schedule_user_kick(user.telegram_id))
    
    async def _send_payment_warning(self, user) -> bool:
        """Отправляет предупреждение о необходимости оплаты."""
        try:
            warning_message = f"""⚠️ <b>ВНИМАНИЕ!</b>

Привет, {user.first_name}!

Твоя подписка на клуб «ОСНОВА ПУТИ» истекла или не была оплачена.

🕐 <b>У тебя есть 3 дня</b> чтобы:
• Оплатить подписку ($33)
• Или связаться с администратором для выдачи доступа

Если в течение 3 дней ты не оплатишь или не получишь доступ от администратора, тебя исключат из группы.

💳 <b>Для оплаты:</b>
1. Нажми /start в личных сообщениях с ботом
2. Выбери "Получить доступ - $33"
3. Оплати любым удобным способом

📞 <b>Для связи с администратором:</b>
Напиши в личные сообщения боту - администратор ответит в течение 24 часов.

⏰ <b>Осталось времени:</b> 3 дня

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
        """Планирует исключение пользователя через 3 дня."""
        try:
            logger.info(f"⏳ Запущена задача исключения для пользователя {telegram_id} - ожидание 3 дня...")
            
            # Ждем 3 дня
            logger.info(f"⏰ Ожидание 3 дня для пользователя {telegram_id}...")
            await asyncio.sleep(3 * 24 * 60 * 60)  # 3 дня в секундах (3 * 24 * 60 * 60)
            
            logger.info(f"⏰ Время ожидания истекло для пользователя {telegram_id} - проверяем оплату...")
            
            # Проверяем, оплатил ли пользователь за это время
            result = await self._kick_user_if_unpaid(telegram_id)
            
            if result:
                logger.info(f"✅ Пользователь {telegram_id} успешно исключен из группы")
            else:
                logger.warning(f"⚠️ Пользователь {telegram_id} НЕ был исключен - возможно, уже оплатил или произошла ошибка")
            
        except Exception as e:
            logger.error(f"Ошибка при планировании исключения пользователя {telegram_id}: {e}")
    
    async def _kick_user_if_unpaid(self, telegram_id: int) -> bool:
        """Исключает пользователя, если он не оплатил."""
        try:
            logger.info(f"🔍 Проверяем статус оплаты для пользователя {telegram_id} перед исключением...")
            
            async with get_db_session() as session:
                user_service = UserService(session)
                
                # Получаем актуальную информацию о пользователе
                user = await user_service.get_user_by_telegram_id(telegram_id)
                
                if not user:
                    logger.warning(f"❌ Пользователь {telegram_id} не найден в базе данных")
                    return False
                
                logger.info(f"📊 Статус пользователя {telegram_id}: {user.status}, Premium: {user.is_premium}, Подписка до: {user.subscription_until}")
                
                # Проверяем, оплатил ли пользователь за это время
                has_active_subscription = (
                    user.status == "active" and 
                    user.is_premium and 
                    user.subscription_until and 
                    user.subscription_until > datetime.utcnow()
                )
                
                if has_active_subscription:
                    logger.info(f"✅ Пользователь {telegram_id} оплатил подписку, исключение отменено")
                    return False
                
                logger.info(f"❌ Пользователь {telegram_id} не оплатил, исключаем из группы...")
                
                # Исключаем пользователя из группы
                result = await self._kick_user_from_group(telegram_id)
                
                if result:
                    # Обновляем статус в базе данных
                    from app.schemas.user import UserUpdate
                    await user_service.update_user(str(user.id), UserUpdate(
                        is_in_group=False,
                        status="pending"
                    ))
                    
                    logger.info(f"🚫 Пользователь {telegram_id} исключен из группы")
                    return True
                else:
                    logger.error(f"❌ Не удалось исключить пользователя {telegram_id}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при исключении пользователя {telegram_id}: {e}")
            import traceback
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return False
    
    async def _kick_user_from_group(self, telegram_id: int) -> bool:
        """Исключает пользователя из группы."""
        try:
            # Исключаем пользователя из группы
            success = await self.telegram_service.kick_chat_member(
                chat_id=int(self.settings.GROUP_ID),
                user_id=telegram_id
            )
            
            if success:
                logger.info(f"✅ Пользователь {telegram_id} успешно исключен из группы")
                return True
            else:
                logger.error(f"❌ Не удалось исключить пользователя {telegram_id} через Telegram API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка исключения пользователя {telegram_id} из группы: {e}")
            return False
    
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
    
    async def auto_add_paid_user_to_group(self, user_id: int) -> bool:
        """
        Автоматически добавляет оплатившего пользователя в группу.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            bool: True если пользователь добавлен успешно
        """
        try:
            async with get_db_session() as session:
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(user_id)
                
                if not user:
                    logger.error(f"Пользователь {user_id} не найден в базе данных")
                    return False
                
                # Проверяем, что у пользователя есть активная подписка
                has_active_subscription = (
                    user.status == "active" and 
                    user.is_premium and 
                    user.subscription_until and 
                    user.subscription_until > datetime.utcnow()
                )
                
                if not has_active_subscription:
                    logger.warning(f"У пользователя {user_id} нет активной подписки")
                    return False
                
                # Если пользователь уже в группе, не нужно его добавлять
                if user.is_in_group:
                    logger.info(f"Пользователь {user_id} уже в группе")
                    return True
                
                # Сначала пытаемся разбанить пользователя (если он был забанен)
                success = await self.add_user_to_group(user_id)
                
                if success:
                    logger.info(f"✅ Пользователь {user_id} автоматически добавлен в группу")
                    return True
                else:
                    # Если разбан не сработал, отправляем приглашение
                    logger.info(f"Пользователь {user_id} не был забанен, отправляем приглашение")
                    return await self._send_group_invite(user_id)
                    
        except Exception as e:
            logger.error(f"Ошибка автоматического добавления пользователя {user_id} в группу: {e}")
            return False
    
    async def _send_group_invite(self, user_id: int) -> bool:
        """
        Отправляет приглашение пользователю в группу.
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            bool: True если приглашение отправлено успешно
        """
        try:
            if not self.telegram_service or not self.telegram_service.bot:
                logger.error("TelegramService не инициализирован")
                return False
            
            # Создаем ссылку-приглашение
            invite_link = await self.telegram_service.create_chat_invite_link()
            if not invite_link:
                logger.error(f"Не удалось создать ссылку-приглашение для пользователя {user_id}")
                return False
            
            # Отправляем приглашение пользователю
            message = f"""
🎉 Добро пожаловать в клуб «ОСНОВА ПУТИ»!

Твоя подписка активирована и ты можешь присоединиться к закрытой группе.

🔗 Ссылка для входа: {invite_link}

Увидимся в группе! 🚀
"""
            
            await self.telegram_service.send_message(user_id, message)
            
            # Обновляем статус в базе данных
            async with get_db_session() as session:
                user_service = UserService(session)
                user = await user_service.get_user_by_telegram_id(user_id)
                
                if user:
                    from app.schemas.user import UserUpdate
                    await user_service.update_user(str(user.id), UserUpdate(
                        is_in_group=True,
                        joined_group_at=datetime.utcnow()
                    ))
            
            logger.info(f"✅ Пользователю {user_id} отправлено приглашение в группу")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки приглашения пользователю {user_id}: {e}")
            return False
    
    async def _sync_group_members_status(self, user_service: UserService) -> None:
        """Синхронизирует статус пользователей в группе с реальным состоянием."""
        try:
            logger.info("🔄 Синхронизируем статус пользователей в группе...")
            
            # Получаем всех пользователей из базы (не только тех, кто в группе)
            all_users = await user_service.get_all_users()
            logger.info(f"📊 Всего пользователей в базе: {len(all_users)}")
            
            # Получаем реальных участников группы через Telegram API
            real_members = await self._get_real_group_members()
            logger.info(f"👥 Реальных участников в группе: {len(real_members)}")
            
            # Обновляем статус в базе
            updated_count = 0
            for user in all_users:
                is_really_in_group = user.telegram_id in real_members
                
                # Если статус не совпадает, обновляем
                if user.is_in_group != is_really_in_group:
                    user.is_in_group = is_really_in_group
                    if is_really_in_group:
                        user.joined_group_at = datetime.utcnow()
                        logger.info(f"✅ Пользователь {user.telegram_id} (@{user.username}) добавлен в группу")
                    else:
                        user.joined_group_at = None
                        logger.info(f"❌ Пользователь {user.telegram_id} (@{user.username}) покинул группу")
                    updated_count += 1
            
            if updated_count > 0:
                await user_service.session.commit()
                logger.info(f"🔄 Обновлено {updated_count} пользователей")
            else:
                logger.info("✅ Статус пользователей актуален")
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации статуса пользователей: {e}")
    
    async def _get_real_group_members(self) -> List[int]:
        """Получает реальный список участников группы через Telegram API."""
        try:
            if not self.telegram_service or not self.telegram_service.bot:
                logger.warning("Бот не инициализирован, пропускаем синхронизацию")
                return []
            
            # Получаем участников группы
            members = []
            try:
                # Получаем количество участников в группе
                chat_member_count = await self.telegram_service.bot.get_chat_member_count(
                    chat_id=int(self.settings.GROUP_ID)
                )
                logger.info(f"📊 Общее количество участников в группе: {chat_member_count}")
                
                # Получаем администраторов (они точно есть в группе)
                administrators = await self.telegram_service.bot.get_chat_administrators(
                    chat_id=int(self.settings.GROUP_ID)
                )
                
                for admin in administrators:
                    if admin.user.id not in members:
                        members.append(admin.user.id)
                        
                logger.info(f"📋 Получено {len(members)} администраторов через API")
                
                # ВАЖНО: Telegram API не позволяет получить полный список участников группы
                # Мы можем получить только администраторов и ботов
                # Поэтому возвращаем только администраторов как "реальных участников"
                # Остальные участники будут добавлены в базу при первом взаимодействии с ботом
                
                return members
                
            except Exception as e:
                logger.error(f"Ошибка получения участников группы через API: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Критическая ошибка получения участников группы: {e}")
            return []
