"""
Схемы Pydantic для системы отслеживания активности.

Этот модуль содержит схемы для валидации данных активности:
- ChatActivity: Активность в чатах
- UserActivity: Сводная активность пользователей
- ActivitySummary: Сводки активности
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from app.models.activity import ActivityType, ActivityPeriod


class ChatActivityCreate(BaseModel):
    """Схема для создания записи активности в чате."""
    
    user_id: str = Field(..., description="ID пользователя")
    chat_id: str = Field(..., description="ID чата Telegram")
    message_id: Optional[int] = Field(None, description="ID сообщения Telegram")
    activity_type: ActivityType = Field(..., description="Тип активности")
    message_text: Optional[str] = Field(None, description="Текст сообщения")
    message_length: int = Field(0, description="Длина сообщения")
    activity_date: date = Field(..., description="Дата активности")
    activity_hour: int = Field(..., ge=0, le=23, description="Час активности")
    is_reply: bool = Field(False, description="Является ли ответом")
    is_forward: bool = Field(False, description="Является ли пересылкой")
    reply_to_user_id: Optional[str] = Field(None, description="ID пользователя ответа")


class ChatActivityResponse(BaseModel):
    """Схема ответа для активности в чате."""
    
    id: str = Field(..., description="ID записи")
    user_id: str = Field(..., description="ID пользователя")
    chat_id: str = Field(..., description="ID чата")
    message_id: Optional[int] = Field(None, description="ID сообщения")
    activity_type: ActivityType = Field(..., description="Тип активности")
    message_text: Optional[str] = Field(None, description="Текст сообщения")
    message_length: int = Field(..., description="Длина сообщения")
    activity_date: date = Field(..., description="Дата активности")
    activity_hour: int = Field(..., description="Час активности")
    is_reply: bool = Field(..., description="Является ли ответом")
    is_forward: bool = Field(..., description="Является ли пересылкой")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class UserActivityCreate(BaseModel):
    """Схема для создания сводной активности пользователя."""
    
    user_id: str = Field(..., description="ID пользователя")
    period_type: ActivityPeriod = Field(..., description="Тип периода")
    period_date: date = Field(..., description="Дата периода")
    total_messages: int = Field(0, description="Всего сообщений")
    text_messages: int = Field(0, description="Текстовых сообщений")
    media_messages: int = Field(0, description="Медиа сообщений")
    total_characters: int = Field(0, description="Всего символов")
    average_message_length: int = Field(0, description="Средняя длина сообщения")
    most_active_hour: Optional[int] = Field(None, description="Самый активный час")
    activity_hours: Optional[str] = Field(None, description="JSON часов активности")
    replies_sent: int = Field(0, description="Отправлено ответов")
    replies_received: int = Field(0, description="Получено ответов")
    forwards_sent: int = Field(0, description="Отправлено пересылок")
    activity_score: int = Field(0, description="Балл активности")


class UserActivityResponse(BaseModel):
    """Схема ответа для сводной активности пользователя."""
    
    id: str = Field(..., description="ID записи")
    user_id: str = Field(..., description="ID пользователя")
    period_type: ActivityPeriod = Field(..., description="Тип периода")
    period_date: date = Field(..., description="Дата периода")
    total_messages: int = Field(..., description="Всего сообщений")
    text_messages: int = Field(..., description="Текстовых сообщений")
    media_messages: int = Field(..., description="Медиа сообщений")
    total_characters: int = Field(..., description="Всего символов")
    average_message_length: int = Field(..., description="Средняя длина сообщения")
    most_active_hour: Optional[int] = Field(None, description="Самый активный час")
    replies_sent: int = Field(..., description="Отправлено ответов")
    replies_received: int = Field(..., description="Получено ответов")
    forwards_sent: int = Field(..., description="Отправлено пересылок")
    activity_score: int = Field(..., description="Балл активности")
    period_rank: Optional[int] = Field(None, description="Ранг за период")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    class Config:
        from_attributes = True


class TopUserSchema(BaseModel):
    """Схема для топ пользователя."""
    
    user_id: str = Field(..., description="ID пользователя")
    telegram_id: int = Field(..., description="Telegram ID")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="Имя")
    display_name: str = Field(..., description="Отображаемое имя")
    total_messages: int = Field(..., description="Всего сообщений")
    activity_score: int = Field(..., description="Балл активности")
    rank: int = Field(..., description="Ранг")


class ActivityStatsResponse(BaseModel):
    """Схема статистики активности за период."""
    
    period_type: ActivityPeriod = Field(..., description="Тип периода")
    period_date: date = Field(..., description="Дата периода")
    total_users: int = Field(..., description="Всего пользователей")
    active_users: int = Field(..., description="Активных пользователей")
    total_messages: int = Field(..., description="Всего сообщений")
    total_characters: int = Field(..., description="Всего символов")
    average_message_length: float = Field(..., description="Средняя длина сообщения")
    engagement_rate: float = Field(..., description="Процент вовлеченности")
    
    # Топ пользователи
    top_users: List[TopUserSchema] = Field(..., description="Топ пользователей")
    connecting_users: List[TopUserSchema] = Field(..., description="Подключающиеся пользователи")
    
    # Распределение активности
    activity_by_hour: Dict[int, int] = Field(..., description="Активность по часам")
    activity_by_type: Dict[str, int] = Field(..., description="Активность по типам")


class WeeklyReportCreate(BaseModel):
    """Схема для создания еженедельного отчета."""
    
    week_start_date: date = Field(..., description="Начало недели")
    week_end_date: date = Field(..., description="Конец недели")
    top_active_users: List[TopUserSchema] = Field(..., description="Топ активных")
    connecting_users: List[TopUserSchema] = Field(..., description="Подключающиеся")
    total_participants: int = Field(..., description="Всего участников")
    active_participants: int = Field(..., description="Активных участников")
    activity_percentage: int = Field(..., description="Процент активности")


class WeeklyReportResponse(BaseModel):
    """Схема ответа для еженедельного отчета."""
    
    id: str = Field(..., description="ID отчета")
    week_start_date: date = Field(..., description="Начало недели")
    week_end_date: date = Field(..., description="Конец недели")
    total_participants: int = Field(..., description="Всего участников")
    active_participants: int = Field(..., description="Активных участников")
    activity_percentage: int = Field(..., description="Процент активности")
    report_message: str = Field(..., description="Готовое сообщение")
    is_published: bool = Field(..., description="Опубликован ли")
    published_at: Optional[datetime] = Field(None, description="Время публикации")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class UserActivityFilter(BaseModel):
    """Фильтр для поиска активности пользователей."""
    
    period_type: Optional[ActivityPeriod] = Field(None, description="Тип периода")
    period_start: Optional[date] = Field(None, description="Начало периода")
    period_end: Optional[date] = Field(None, description="Конец периода")
    user_ids: Optional[List[str]] = Field(None, description="Список ID пользователей")
    min_messages: Optional[int] = Field(None, description="Минимум сообщений")
    limit: int = Field(50, ge=1, le=1000, description="Лимит результатов")
    offset: int = Field(0, ge=0, description="Смещение")


class ActivityAnalysisRequest(BaseModel):
    """Запрос на анализ активности."""
    
    chat_id: Optional[str] = Field(None, description="ID чата")
    period_type: ActivityPeriod = Field(..., description="Тип периода")
    start_date: date = Field(..., description="Начальная дата")
    end_date: Optional[date] = Field(None, description="Конечная дата")
    include_stats: bool = Field(True, description="Включить статистику")
    include_ranking: bool = Field(True, description="Включить рейтинг")
    top_limit: int = Field(10, ge=1, le=50, description="Количество в топе")


class ActivityTrendResponse(BaseModel):
    """Схема ответа для трендов активности."""
    
    period_dates: List[date] = Field(..., description="Даты периодов")
    message_counts: List[int] = Field(..., description="Количество сообщений")
    user_counts: List[int] = Field(..., description="Количество пользователей")
    engagement_rates: List[float] = Field(..., description="Проценты вовлеченности")
    growth_rates: List[float] = Field(..., description="Темпы роста")
    
    # Статистические показатели
    average_growth: float = Field(..., description="Средний темп роста")
    trend_direction: str = Field(..., description="Направление тренда")
    stability_score: float = Field(..., description="Показатель стабильности")

