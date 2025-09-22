"""
Сервис для работы с платежами.

Содержит бизнес-логику для управления платежами и интеграции с FreeKassa.
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from loguru import logger
import httpx

from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentUpdate
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings
from app.core.exceptions import PaymentException, FreeKassaException


class PaymentService:
    """Сервис для работы с платежами."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """
        Создание нового платежа.
        
        Args:
            payment_data: Данные для создания платежа
            
        Returns:
            Payment: Созданный платеж
            
        Raises:
            PaymentException: Если не удалось создать платеж
        """
        try:
            # Проверяем, существует ли пользователь
            user = await self._get_user_by_id(payment_data.user_id)
            if not user:
                raise PaymentException(f"Пользователь с ID {payment_data.user_id} не найден")
            
            # Создаем платеж в базе данных
            payment = Payment(**payment_data.dict())
            self.session.add(payment)
            await self.session.commit()
            await self.session.refresh(payment)
            
            # Payment system integration disabled for now
            # freekassa_data = await self._create_freekassa_payment(payment)
            # await self._update_payment_with_freekassa_data(payment.id, freekassa_data)
            
            # For now, just set a placeholder URL
            payment.payment_url = "https://example.com/payment-disabled"
            
            logger.info(f"Создан платеж: {payment.id} для пользователя {user.telegram_id}")
            return payment
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка создания платежа: {e}")
            raise PaymentException(f"Не удалось создать платеж: {e}")
    
    async def get_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """
        Получение платежа по ID.
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Optional[Payment]: Платеж или None
        """
        try:
            result = await self.session.execute(
                select(Payment).where(Payment.id == payment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения платежа по ID {payment_id}: {e}")
            return None
    
    async def get_payment_by_external_id(self, external_id: str) -> Optional[Payment]:
        """
        Получение платежа по внешнему ID (например, invoice_id от CryptoBot).
        
        Args:
            external_id: Внешний ID платежа
            
        Returns:
            Optional[Payment]: Платеж или None
        """
        try:
            result = await self.session.execute(
                select(Payment).where(Payment.external_id == external_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения платежа по внешнему ID {external_id}: {e}")
            return None
    
    # Disabled FreeKassa methods
    # async def get_payment_by_freekassa_id(self, freekassa_payment_id: str) -> Optional[Payment]:
        """
        Получение платежа по ID в FreeKassa.
        
        Args:
            freekassa_payment_id: ID платежа в FreeKassa
            
        Returns:
            Optional[Payment]: Платеж или None
        """
        try:
            result = await self.session.execute(
                select(Payment).where(Payment.freekassa_payment_id == freekassa_payment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения платежа по FreeKassa ID {freekassa_payment_id}: {e}")
            return None
    
    async def update_payment_status(self, payment_id: str, status: PaymentStatus) -> bool:
        """
        Обновление статуса платежа.
        
        Args:
            payment_id: ID платежа
            status: Новый статус
            
        Returns:
            bool: True если успешно обновлен
        """
        try:
            payment = await self.get_payment_by_id(payment_id)
            if not payment:
                raise PaymentException(f"Платеж с ID {payment_id} не найден")
            
            # Обновляем статус
            await self.session.execute(
                update(Payment).where(Payment.id == payment_id).values(
                    status=status,
                    paid_at=datetime.utcnow() if status == PaymentStatus.PAID else None
                )
            )
            await self.session.commit()
            
            logger.info(f"Обновлен статус платежа {payment_id}: {status}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления статуса платежа {payment_id}: {e}")
            return False
    
    # async def process_freekassa_webhook(self, webhook_data: FreeKassaWebhook) -> bool:
        """
        Обработка webhook от FreeKassa.
        
        Args:
            webhook_data: Данные webhook от FreeKassa
            
        Returns:
            bool: True если webhook обработан успешно
        """
        try:
            # Проверяем подпись
            if not self._verify_freekassa_signature(webhook_data):
                raise FreeKassaException("Неверная подпись webhook")
            
            # Получаем платеж
            payment = await self.get_payment_by_freekassa_id(webhook_data.payment_id)
            if not payment:
                raise PaymentException(f"Платеж с FreeKassa ID {webhook_data.payment_id} не найден")
            
            # Проверяем сумму
            if str(payment.amount) != webhook_data.amount:
                raise PaymentException(f"Неверная сумма платежа: ожидалось {payment.amount}, получено {webhook_data.amount}")
            
            # Обновляем статус платежа
            if webhook_data.status == "paid":
                await self.update_payment_status(payment.id, PaymentStatus.PAID)
                
                # Отправляем уведомление об успешной оплате
                # await self._add_user_to_group_after_payment(payment.user_id)  # Пока отключено
                
                logger.info(f"Платеж {payment.id} успешно обработан, подписка активирована")
            else:
                await self.update_payment_status(payment.id, PaymentStatus.FAILED)
                logger.warning(f"Платеж {payment.id} не прошел: {webhook_data.status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook FreeKassa: {e}")
            return False
    
    # async def _create_freekassa_payment(self, payment: Payment) -> Dict[str, Any]:
        """
        Создание платежа в FreeKassa.
        
        Args:
            payment: Платеж для создания
            
        Returns:
            Dict[str, Any]: Данные от FreeKassa
            
        Raises:
            FreeKassaException: Если не удалось создать платеж в FreeKassa
        """
        try:
            # Получаем пользователя
            user = await self._get_user_by_id(str(payment.user_id))
            
            # Формируем данные для FreeKassa
            order_id = str(payment.id)
            amount = str(payment.amount)
            
            # Создаем подпись
            signature_data = f"{settings.freekassa_shop_id}:{amount}:{settings.freekassa_secret_key}:{order_id}"
            signature = hashlib.md5(signature_data.encode()).hexdigest()
            
            # Данные для запроса
            request_data = {
                "shop_id": settings.freekassa_shop_id,
                "amount": amount,
                "currency": payment.currency,
                "order_id": order_id,
                "signature": signature,
                "payment_method": "card",  # Можно сделать настраиваемым
                "description": payment.description or f"Платеж для пользователя {user.telegram_id}"
            }
            
            # Отправляем запрос к FreeKassa
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.freekassa.ru/v1/orders",
                    json=request_data,
                    headers={"Authorization": f"Bearer {settings.freekassa_api_key}"}
                )
                
                if response.status_code != 200:
                    raise FreeKassaException(f"Ошибка FreeKassa API: {response.status_code} - {response.text}")
                
                data = response.json()
                
                if data.get("status") != "success":
                    raise FreeKassaException(f"Ошибка создания платежа в FreeKassa: {data.get('message')}")
                
                return data.get("data", {})
                
        except Exception as e:
            logger.error(f"Ошибка создания платежа в FreeKassa: {e}")
            raise FreeKassaException(f"Не удалось создать платеж в FreeKassa: {e}")
    
    # async def _update_payment_with_freekassa_data(self, payment_id: str, freekassa_data: Dict[str, Any]) -> None:
        """
        Обновление платежа данными от FreeKassa.
        
        Args:
            payment_id: ID платежа
            freekassa_data: Данные от FreeKassa
        """
        try:
            update_data = {
                "freekassa_payment_id": freekassa_data.get("payment_id"),
                "freekassa_order_id": freekassa_data.get("order_id"),
                "payment_url": freekassa_data.get("payment_url"),
                "freekassa_data": json.dumps(freekassa_data)
            }
            
            await self.session.execute(
                update(Payment).where(Payment.id == payment_id).values(**update_data)
            )
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Ошибка обновления платежа данными FreeKassa: {e}")
    
    # def _verify_freekassa_signature(self, webhook_data: FreeKassaWebhook) -> bool:
        """
        Проверка подписи webhook от FreeKassa.
        
        Args:
            webhook_data: Данные webhook
            
        Returns:
            bool: True если подпись верна
        """
        try:
            # Формируем строку для подписи
            signature_data = f"{webhook_data.shop_id}:{webhook_data.amount}:{settings.freekassa_secret_key}:{webhook_data.order_id}"
            expected_signature = hashlib.md5(signature_data.encode()).hexdigest()
            
            return webhook_data.signature.lower() == expected_signature.lower()
            
        except Exception as e:
            logger.error(f"Ошибка проверки подписи FreeKassa: {e}")
            return False
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя (строка)
            
        Returns:
            Optional[User]: Пользователь или None
        """
        try:
            # Конвертируем строку обратно в UUID для запроса
            uuid_obj = UUID(user_id) if isinstance(user_id, str) else user_id
            result = await self.session.execute(
                select(User).where(User.id == uuid_obj)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по ID {user_id}: {e}")
            return None
    
    # Временно отключено - направляем только на канал
    # async def _add_user_to_group_after_payment(self, user_id: str) -> bool:
    #     """
    #     Добавление пользователя в группу после успешной оплаты.
    #     
    #     Args:
    #         user_id: ID пользователя
    #         
    #     Returns:
    #         bool: True если успешно добавлен
    #     """
    #     try:
    #         # Здесь будет логика добавления в Telegram группу
    #         # Пока просто обновляем статус пользователя
    #         user = await self._get_user_by_id(user_id)
    #         if user:
    #             await self.session.execute(
    #                 update(User).where(User.id == user_id).values(
    #                     status="active",
    #                     is_in_group=True,
    #                     joined_group_at=datetime.utcnow()
    #                 )
    #             )
    #             await self.session.commit()
    #             
    #             logger.info(f"Пользователь {user_id} добавлен в группу после оплаты")
    #             return True
    #         
    #         return False
    #         
    #     except Exception as e:
    #         await self.session.rollback()
    #         logger.error(f"Ошибка добавления пользователя {user_id} в группу после оплаты: {e}")
    #         return False
    
    async def get_user_payments(self, user_id: str) -> List[Payment]:
        """
        Получение платежей пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Payment]: Список платежей пользователя
        """
        try:
            result = await self.session.execute(
                select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения платежей пользователя {user_id}: {e}")
            return []
    
    async def get_payments(self, limit: int = 100, status: Optional[PaymentStatus] = None) -> List[Payment]:
        """
        Получение списка платежей с фильтрацией.
        
        Args:
            limit: Максимальное количество записей
            status: Фильтр по статусу
            
        Returns:
            List[Payment]: Список платежей
        """
        try:
            query = select(Payment)
            
            if status:
                query = query.where(Payment.status == status)
            
            query = query.order_by(Payment.created_at.desc()).limit(limit)
            result = await self.session.execute(query)
            
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Ошибка получения списка платежей: {e}")
            return []

    async def get_payments_count(self) -> int:
        """
        Получить общее количество платежей.
        
        Returns:
            int: Количество платежей
        """
        try:
            stmt = select(func.count(Payment.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества платежей: {e}")
            return 0

    async def get_total_revenue(self) -> float:
        """
        Получить общую сумму доходов.
        
        Returns:
            float: Общая сумма доходов
        """
        try:
            stmt = select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.PAID)
            result = await self.session.execute(stmt)
            return result.scalar() or 0.0
        except Exception as e:
            logger.error(f"Ошибка получения общего дохода: {e}")
            return 0.0

    async def get_recent_payments(self, limit: int = 10) -> List[Payment]:
        """
        Получить список последних платежей.
        
        Args:
            limit: Максимальное количество платежей
            
        Returns:
            List[Payment]: Список последних платежей
        """
        try:
            stmt = (
                select(Payment)
                .options(selectinload(Payment.user))
                .order_by(Payment.created_at.desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения последних платежей: {e}")
            return []
    
    async def get_total_payments_count(self) -> int:
        """Получение общего количества платежей."""
        try:
            stmt = select(func.count(Payment.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Ошибка получения общего количества платежей: {e}")
            return 0
    
    async def get_successful_payments_count(self) -> int:
        """Получение количества успешных платежей."""
        try:
            stmt = select(func.count(Payment.id)).where(Payment.status == PaymentStatus.PAID)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Ошибка получения количества успешных платежей: {e}")
            return 0
    
    async def get_total_payments_amount(self) -> Decimal:
        """Получение общей суммы платежей."""
        try:
            stmt = select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.PAID)
            result = await self.session.execute(stmt)
            return result.scalar() or Decimal('0')
        except Exception as e:
            logger.error(f"Ошибка получения общей суммы платежей: {e}")
            return Decimal('0')
    
    async def get_today_payments_amount(self) -> Decimal:
        """Получение суммы платежей за сегодня."""
        try:
            today = datetime.utcnow().date()
            stmt = select(func.sum(Payment.amount)).where(
                and_(
                    Payment.status == PaymentStatus.PAID,
                    func.date(Payment.paid_at) == today
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar() or Decimal('0')
        except Exception as e:
            logger.error(f"Ошибка получения суммы платежей за сегодня: {e}")
            return Decimal('0')
