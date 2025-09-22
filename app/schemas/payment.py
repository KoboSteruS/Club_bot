"""
Схемы для платежей.

Содержит Pydantic модели для валидации данных платежей.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator

from app.models.payment import PaymentStatus


class PaymentBase(BaseModel):
    """Базовая схема платежа."""
    
    amount: Decimal = Field(..., description="Сумма платежа")
    currency: str = Field(default="RUB", description="Валюта платежа")
    description: Optional[str] = Field(None, description="Описание платежа")
    external_id: Optional[str] = Field(None, description="Внешний ID платежа")
    
    @validator("amount")
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Валидация суммы платежа."""
        if v <= 0:
            raise ValueError("Сумма платежа должна быть больше нуля")
        return v
    
    @validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Валидация валюты."""
        if len(v) < 3 or len(v) > 4:
            raise ValueError("Код валюты должен состоять из 3-4 символов")
        return v.upper()


class PaymentCreate(PaymentBase):
    """Схема для создания платежа."""
    
    user_id: str = Field(..., description="ID пользователя")


class PaymentUpdate(BaseModel):
    """Схема для обновления платежа."""
    
    status: Optional[PaymentStatus] = Field(None, description="Статус платежа")
    # freekassa_payment_id: Optional[str] = Field(None, description="ID платежа в FreeKassa")
    # freekassa_order_id: Optional[str] = Field(None, description="ID заказа в FreeKassa")
    payment_url: Optional[str] = Field(None, description="URL для оплаты")
    paid_at: Optional[datetime] = Field(None, description="Дата оплаты")
    # freekassa_data: Optional[str] = Field(None, description="Дополнительные данные от FreeKassa")


class PaymentResponse(PaymentBase):
    """Схема для ответа с данными платежа."""
    
    id: str = Field(..., description="Уникальный идентификатор платежа")
    user_id: str = Field(..., description="ID пользователя")
    status: PaymentStatus = Field(..., description="Статус платежа")
    # freekassa_payment_id: Optional[str] = Field(None, description="ID платежа в FreeKassa")
    # freekassa_order_id: Optional[str] = Field(None, description="ID заказа в FreeKassa")
    payment_url: Optional[str] = Field(None, description="URL для оплаты")
    paid_at: Optional[datetime] = Field(None, description="Дата оплаты")
    # freekassa_data: Optional[str] = Field(None, description="Дополнительные данные от FreeKassa")
    created_at: datetime = Field(..., description="Дата создания записи")
    updated_at: datetime = Field(..., description="Дата последнего обновления")
    
    class Config:
        from_attributes = True


class PaymentList(BaseModel):
    """Схема для списка платежей."""
    
    payments: list[PaymentResponse] = Field(..., description="Список платежей")
    total: int = Field(..., description="Общее количество платежей")
    page: int = Field(..., description="Номер страницы")
    per_page: int = Field(..., description="Количество записей на странице")


# Payment system webhooks (disabled for now)
# class FreeKassaWebhook(BaseModel):
#     """Схема для webhook от FreeKassa."""
#     
#     shop_id: str = Field(..., description="ID магазина")
#     amount: str = Field(..., description="Сумма платежа")
#     currency: str = Field(..., description="Валюта платежа")
#     order_id: str = Field(..., description="ID заказа")
#     payment_id: str = Field(..., description="ID платежа")
#     signature: str = Field(..., description="Подпись для проверки")
#     status: str = Field(..., description="Статус платежа")
#     
#     class Config:
#         extra = "allow"  # Разрешаем дополнительные поля
