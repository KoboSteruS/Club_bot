"""
Сервис для массовых операций с пользователями.

Оптимизирует производительность при работе с большим количеством пользователей.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.core.database import get_db_session
from app.services.user_service import UserService
from app.services.telegram_service import TelegramService
from telegram import Bot
from config.settings import get_settings


class BatchService:
    """Сервис для массовых операций."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.settings = get_settings()
        self.bot = Bot(token=self.settings.TELEGRAM_BOT_TOKEN)
        self.telegram_service = TelegramService(self.bot)
        
    async def send_messages_batch(
        self, 
        user_ids: List[int], 
        message: str, 
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> Dict[str, int]:
        """
        Отправка сообщений пакетами для оптимизации производительности.
        
        Args:
            user_ids: Список ID пользователей
            message: Текст сообщения
            batch_size: Размер пакета
            delay_between_batches: Задержка между пакетами в секундах
            
        Returns:
            Dict с результатами отправки
        """
        results = {
            'sent': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Разбиваем на пакеты
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            
            # Отправляем сообщения в пакете параллельно
            tasks = [
                self._send_message_with_retry(user_id, message)
                for user_id in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Подсчитываем результаты
            for result in batch_results:
                if isinstance(result, Exception):
                    results['failed'] += 1
                    logger.error(f"Ошибка отправки сообщения: {result}")
                elif result is True:
                    results['sent'] += 1
                elif result is False:
                    results['skipped'] += 1
                else:
                    results['failed'] += 1
            
            # Задержка между пакетами
            if i + batch_size < len(user_ids):
                await asyncio.sleep(delay_between_batches)
                
        logger.info(f"Отправка завершена: отправлено {results['sent']}, "
                   f"пропущено {results['skipped']}, ошибок {results['failed']}")
        
        return results
    
    async def _send_message_with_retry(
        self, 
        user_id: int, 
        message: str, 
        max_retries: int = 3
    ) -> Optional[bool]:
        """
        Отправка сообщения с повторными попытками.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            max_retries: Максимальное количество попыток
            
        Returns:
            True если отправлено, False если пропущено, None при ошибке
        """
        for attempt in range(max_retries):
            try:
                success = await self.telegram_service.send_message(user_id, message)
                return success
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Не удалось отправить сообщение пользователю {user_id} "
                               f"после {max_retries} попыток: {e}")
                    return None
                else:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Экспоненциальная задержка
        
        return None
    
    async def get_active_users_batch(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Получение списка активных пользователей пакетами.
        
        Args:
            limit: Максимальное количество пользователей
            
        Returns:
            Список активных пользователей
        """
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Получаем активных пользователей
            users = await user_service.get_active_users(limit=limit)
            
            return [
                {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'status': user.status,
                    'is_premium': user.is_premium,
                    'created_at': user.created_at
                }
                for user in users
            ]
    
    async def update_users_subscription_status_batch(
        self, 
        user_ids: List[int], 
        batch_size: int = 50
    ) -> Dict[str, int]:
        """
        Обновление статуса подписки пользователей пакетами.
        
        Args:
            user_ids: Список ID пользователей
            batch_size: Размер пакета
            
        Returns:
            Dict с результатами обновления
        """
        results = {
            'updated': 0,
            'failed': 0,
            'not_found': 0
        }
        
        async with get_db_session() as session:
            user_service = UserService(session)
            
            # Разбиваем на пакеты
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i:i + batch_size]
                
                # Обновляем статус подписки для пакета
                for user_id in batch:
                    try:
                        user = await user_service.get_user_by_telegram_id(user_id)
                        if user:
                            # Проверяем подписку на канал
                            is_subscribed = await self.telegram_service.check_user_subscription(
                                user_id, 
                                self.settings.CHANNEL_ID
                            )
                            
                            # Обновляем статус в базе данных
                            await user_service.update_user(
                                user.id,
                                {'is_subscribed_to_channel': is_subscribed}
                            )
                            
                            results['updated'] += 1
                        else:
                            results['not_found'] += 1
                    except Exception as e:
                        logger.error(f"Ошибка обновления статуса пользователя {user_id}: {e}")
                        results['failed'] += 1
                
                # Небольшая задержка между пакетами
                if i + batch_size < len(user_ids):
                    await asyncio.sleep(0.5)
        
        logger.info(f"Обновление статуса подписки завершено: обновлено {results['updated']}, "
                   f"не найдено {results['not_found']}, ошибок {results['failed']}")
        
        return results
