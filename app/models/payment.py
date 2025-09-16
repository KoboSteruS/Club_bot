"""
Модель платежа.

Содержит информацию о платежах пользователей.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import BigInteger, DateTime, Numeric, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class PaymentStatus(str, Enum):
    """Статусы платежа."""
    
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentTariff(str, Enum):
    """Тарифы подписки."""
    
    ONE_MONTH = "1_month"
    THREE_MONTHS = "3_months"
    SUBSCRIPTION = "subscription"


class Payment(BaseModel):
    """Модель платежа."""
    
    __tablename__ = "payments"
    
    # ID пользователя (связь с таблицей users)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        doc="ID пользователя"
    )
    
    # Сумма платежа
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        doc="Сумма платежа"
    )
    
    # Валюта платежа
    currency: Mapped[str] = mapped_column(
        String(3),
        default="RUB",
        nullable=False,
        doc="Валюта платежа"
    )
    
    # Тариф подписки
    tariff: Mapped[PaymentTariff] = mapped_column(
        String(20),
        default=PaymentTariff.ONE_MONTH,
        nullable=False,
        doc="Тариф подписки"
    )
    
    # Дата начала подписки
    subscription_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Дата начала подписки"
    )
    
    # Дата окончания подписки
    subscription_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Дата окончания подписки"
    )
    
    # Статус платежа
    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        default=PaymentStatus.PENDING,
        nullable=False,
        doc="Статус платежа"
    )
    
    # Описание платежа
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Описание платежа"
    )
    
    # Payment system fields (disabled for now)
    # freekassa_payment_id: Mapped[str] = mapped_column(
    #     String(255),
    #     nullable=True,
    #     index=True,
    #     doc="ID платежа в FreeKassa"
    # )
    
    # freekassa_order_id: Mapped[str] = mapped_column(
    #     String(255),
    #     nullable=True,
    #     index=True,
    #     doc="ID заказа в FreeKassa"
    # )
    
    # URL для оплаты
    payment_url: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="URL для оплаты"
    )
    
    # Дата оплаты
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Дата оплаты"
    )
    
    # Additional payment data (disabled for now)
    # freekassa_data: Mapped[str] = mapped_column(
    #     Text,
    #     nullable=True,
    #     doc="Дополнительные данные от FreeKassa"
    # )
    
    # Связь с пользователем
    user = relationship("User", back_populates="payments")
    
    def __repr__(self) -> str:
        """Строковое представление платежа."""
        return f"<Payment(id={self.id}, amount={self.amount} {self.currency}, status={self.status})>"
    
    @property
    def is_paid(self) -> bool:
        """Проверка, оплачен ли платеж."""
        return self.status == PaymentStatus.PAID
    
    @property
    def is_pending(self) -> bool:
        """Проверка, ожидает ли платеж оплаты."""
        return self.status == PaymentStatus.PENDING
    
    @property
    def is_failed(self) -> bool:
        """Проверка, неудачен ли платеж."""
        return self.status in [PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.EXPIRED]
