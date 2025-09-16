"""
Схемы Pydantic для системы ритуалов.

Этот модуль содержит схемы для валидации данных ритуалов:
- Ritual: Конфигурация ритуалов
- UserRitual: Участие пользователей
- RitualResponse: Ответы на ритуалы
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator

from app.models.ritual import RitualType, RitualSchedule, ResponseType


class RitualButtonSchema(BaseModel):
    """Схема для кнопки ответа на ритуал."""
    
    text: str = Field(..., description="Текст кнопки")
    callback_data: str = Field(..., description="Данные для callback")
    response_type: ResponseType = Field(..., description="Тип ответа")


class RitualCreate(BaseModel):
    """Схема для создания ритуала."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Название ритуала")
    description: Optional[str] = Field(None, description="Описание ритуала")
    type: RitualType = Field(..., description="Тип ритуала")
    schedule: RitualSchedule = Field(..., description="Расписание")
    
    # Время отправки
    send_hour: int = Field(..., ge=0, le=23, description="Час отправки (0-23)")
    send_minute: int = Field(0, ge=0, le=59, description="Минута отправки (0-59)")
    weekday: Optional[int] = Field(None, ge=0, le=6, description="День недели для еженедельных ритуалов")
    
    # Контент
    message_title: str = Field(..., min_length=1, max_length=500, description="Заголовок сообщения")
    message_text: str = Field(..., min_length=1, description="Текст сообщения")
    response_buttons: Optional[List[RitualButtonSchema]] = Field(None, description="Кнопки ответа")
    
    # Настройки
    is_active: bool = Field(True, description="Активен ли ритуал")
    requires_subscription: bool = Field(True, description="Требует ли активную подписку")
    sort_order: int = Field(0, description="Порядок сортировки")
    
    @validator('weekday')
    def validate_weekday(cls, v, values):
        """Валидация дня недели для еженедельных ритуалов."""
        if values.get('schedule') == RitualSchedule.WEEKLY and v is None:
            raise ValueError('Для еженедельных ритуалов необходимо указать день недели')
        if values.get('schedule') != RitualSchedule.WEEKLY and v is not None:
            raise ValueError('День недели указывается только для еженедельных ритуалов')
        return v


class RitualUpdate(BaseModel):
    """Схема для обновления ритуала."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Название ритуала")
    description: Optional[str] = Field(None, description="Описание ритуала")
    type: Optional[RitualType] = Field(None, description="Тип ритуала")
    schedule: Optional[RitualSchedule] = Field(None, description="Расписание")
    
    # Время отправки
    send_hour: Optional[int] = Field(None, ge=0, le=23, description="Час отправки (0-23)")
    send_minute: Optional[int] = Field(None, ge=0, le=59, description="Минута отправки (0-59)")
    weekday: Optional[int] = Field(None, ge=0, le=6, description="День недели")
    
    # Контент
    message_title: Optional[str] = Field(None, min_length=1, max_length=500, description="Заголовок сообщения")
    message_text: Optional[str] = Field(None, min_length=1, description="Текст сообщения")
    response_buttons: Optional[List[RitualButtonSchema]] = Field(None, description="Кнопки ответа")
    
    # Настройки
    is_active: Optional[bool] = Field(None, description="Активен ли ритуал")
    requires_subscription: Optional[bool] = Field(None, description="Требует ли активную подписку")
    sort_order: Optional[int] = Field(None, description="Порядок сортировки")


class RitualResponse(BaseModel):
    """Схема ритуала для ответа."""
    
    id: str = Field(..., description="ID ритуала")
    name: str = Field(..., description="Название ритуала")
    description: Optional[str] = Field(None, description="Описание ритуала")
    type: RitualType = Field(..., description="Тип ритуала")
    schedule: RitualSchedule = Field(..., description="Расписание")
    
    # Время отправки
    send_hour: int = Field(..., description="Час отправки")
    send_minute: int = Field(..., description="Минута отправки")
    weekday: Optional[int] = Field(None, description="День недели")
    
    # Контент
    message_title: str = Field(..., description="Заголовок сообщения")
    message_text: str = Field(..., description="Текст сообщения")
    response_buttons: Optional[List[RitualButtonSchema]] = Field(None, description="Кнопки ответа")
    
    # Настройки
    is_active: bool = Field(..., description="Активен ли ритуал")
    requires_subscription: bool = Field(..., description="Требует ли активную подписку")
    sort_order: int = Field(..., description="Порядок сортировки")
    
    # Метаданные
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    class Config:
        from_attributes = True


class UserRitualCreate(BaseModel):
    """Схема для создания участия пользователя в ритуале."""
    
    user_id: str = Field(..., description="ID пользователя")
    ritual_id: str = Field(..., description="ID ритуала")
    is_enabled: bool = Field(True, description="Включен ли ритуал для пользователя")
    timezone_offset: int = Field(3, description="Смещение часового пояса")


class UserRitualUpdate(BaseModel):
    """Схема для обновления участия пользователя в ритуале."""
    
    is_enabled: Optional[bool] = Field(None, description="Включен ли ритуал")
    timezone_offset: Optional[int] = Field(None, description="Смещение часового пояса")


class UserRitualResponse(BaseModel):
    """Схема участия пользователя в ритуале для ответа."""
    
    id: str = Field(..., description="ID участия")
    user_id: str = Field(..., description="ID пользователя")
    ritual_id: str = Field(..., description="ID ритуала")
    
    # Статистика
    last_sent_at: Optional[datetime] = Field(None, description="Последняя отправка")
    total_sent: int = Field(..., description="Всего отправлено")
    total_responses: int = Field(..., description="Всего ответов")
    total_completed: int = Field(..., description="Всего выполнено")
    total_skipped: int = Field(..., description="Всего пропущено")
    
    # Настройки
    is_enabled: bool = Field(..., description="Включен ли ритуал")
    timezone_offset: int = Field(..., description="Смещение часового пояса")
    
    # Метаданные
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    class Config:
        from_attributes = True


class RitualResponseCreate(BaseModel):
    """Схема для создания ответа на ритуал."""
    
    user_ritual_id: str = Field(..., description="ID участия в ритуале")
    ritual_id: str = Field(..., description="ID ритуала")
    response_type: ResponseType = Field(..., description="Тип ответа")
    response_text: Optional[str] = Field(None, description="Текст ответа")
    button_clicked: Optional[str] = Field(None, description="Нажатая кнопка")
    sent_at: datetime = Field(..., description="Время отправки ритуала")


class RitualResponseResponse(BaseModel):
    """Схема ответа на ритуал для ответа."""
    
    id: str = Field(..., description="ID ответа")
    user_ritual_id: str = Field(..., description="ID участия в ритуале")
    ritual_id: str = Field(..., description="ID ритуала")
    
    # Ответ
    response_type: ResponseType = Field(..., description="Тип ответа")
    response_text: Optional[str] = Field(None, description="Текст ответа")
    button_clicked: Optional[str] = Field(None, description="Нажатая кнопка")
    
    # Время
    sent_at: datetime = Field(..., description="Время отправки")
    responded_at: Optional[datetime] = Field(None, description="Время ответа")
    
    # Метаданные
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    class Config:
        from_attributes = True


class RitualStatsResponse(BaseModel):
    """Схема статистики ритуала."""
    
    ritual_id: str = Field(..., description="ID ритуала")
    ritual_name: str = Field(..., description="Название ритуала")
    
    # Общая статистика
    total_participants: int = Field(..., description="Всего участников")
    active_participants: int = Field(..., description="Активных участников")
    
    # Статистика отправки
    total_sent: int = Field(..., description="Всего отправлено")
    total_responses: int = Field(..., description="Всего ответов")
    total_completed: int = Field(..., description="Всего выполнено")
    total_skipped: int = Field(..., description="Всего пропущено")
    
    # Процентные показатели
    response_rate: float = Field(..., description="Процент ответивших")
    completion_rate: float = Field(..., description="Процент выполнивших")
    
    # Последняя активность
    last_sent_at: Optional[datetime] = Field(None, description="Последняя отправка")
    
    class Config:
        from_attributes = True

