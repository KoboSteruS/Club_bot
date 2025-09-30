"""
Модели для отслеживания активности пользователей в чатах.

Этот модуль содержит модели для:
- ChatActivity: Активность в чатах
- UserActivity: Сводная активность пользователей
- ActivityPeriod: Периоды активности для статистики
"""

from datetime import datetime, date
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import BaseModel


class ActivityType(str, Enum):
    """Тип активности в чате."""
    MESSAGE = "message"           # Обычное текстовое сообщение
    PHOTO = "photo"              # Фото
    VIDEO = "video"              # Видео
    VIDEO_NOTE = "video_note"    # Видеосообщение (круглое)
    VOICE = "voice"              # Голосовое сообщение
    AUDIO = "audio"              # Аудиофайл
    DOCUMENT = "document"        # Документ
    STICKER = "sticker"          # Стикер
    ANIMATION = "animation"      # GIF анимация
    POLL = "poll"                # Опрос
    LOCATION = "location"        # Геолокация
    CONTACT = "contact"          # Контакт
    GAME = "game"                # Игра
    INVOICE = "invoice"          # Инвойс
    SUCCESSFUL_PAYMENT = "successful_payment"  # Успешный платеж
    FORWARD = "forward"          # Пересланное сообщение
    REPLY = "reply"              # Ответ на сообщение
    EDIT = "edit"                # Редактирование сообщения
    DELETE = "delete"            # Удаление сообщения


class ActivityPeriod(str, Enum):
    """Период для анализа активности."""
    DAILY = "daily"              # Ежедневная статистика
    WEEKLY = "weekly"            # Еженедельная статистика
    MONTHLY = "monthly"          # Месячная статистика


class ChatActivity(BaseModel):
    """
    Модель для отслеживания активности в чатах.
    
    Сохраняет каждое действие пользователя в группе
    для последующего анализа и построения статистики.
    """
    __tablename__ = "chat_activities"

    # Основная информация
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="ID пользователя")
    chat_id = Column(String(50), nullable=False, comment="ID чата Telegram")
    message_id = Column(Integer, nullable=True, comment="ID сообщения Telegram")
    
    # Тип активности
    activity_type = Column(SQLEnum(ActivityType), nullable=False, comment="Тип активности")
    
    # Содержимое (опционально)
    message_text = Column(Text, nullable=True, comment="Текст сообщения")
    message_length = Column(Integer, default=0, comment="Длина сообщения в символах")
    
    # Временная информация
    activity_date = Column(Date, nullable=False, comment="Дата активности")
    activity_hour = Column(Integer, nullable=False, comment="Час активности (0-23)")
    
    # Дополнительная информация
    is_reply = Column(Boolean, default=False, comment="Является ли ответом")
    is_forward = Column(Boolean, default=False, comment="Является ли пересылкой")
    reply_to_user_id = Column(String(36), nullable=True, comment="ID пользователя, на которого отвечают")
    
    # Медиа-контент
    media_file_id = Column(String(100), nullable=True, comment="ID медиафайла в Telegram")
    media_duration = Column(Integer, nullable=True, comment="Длительность аудио/видео в секундах")
    media_file_size = Column(Integer, nullable=True, comment="Размер файла в байтах")
    
    # Связи
    user = relationship("User", back_populates="chat_activities")


class UserActivity(BaseModel):
    """
    Модель сводной активности пользователя.
    
    Агрегированная статистика активности пользователя
    за определенный период (день/неделя/месяц).
    """
    __tablename__ = "user_activities"

    # Основная информация
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="ID пользователя")
    period_type = Column(SQLEnum(ActivityPeriod), nullable=False, comment="Тип периода")
    period_date = Column(Date, nullable=False, comment="Дата периода")
    
    # Статистика сообщений
    total_messages = Column(Integer, default=0, comment="Всего сообщений")
    text_messages = Column(Integer, default=0, comment="Текстовых сообщений")
    media_messages = Column(Integer, default=0, comment="Медиа сообщений")
    
    # Статистика активности
    total_characters = Column(Integer, default=0, comment="Всего символов")
    average_message_length = Column(Integer, default=0, comment="Средняя длина сообщения")
    
    # Время активности
    most_active_hour = Column(Integer, nullable=True, comment="Самый активный час")
    activity_hours = Column(String(100), nullable=True, comment="JSON с часами активности")
    
    # Взаимодействие
    replies_sent = Column(Integer, default=0, comment="Отправлено ответов")
    replies_received = Column(Integer, default=0, comment="Получено ответов")
    forwards_sent = Column(Integer, default=0, comment="Отправлено пересылок")
    
    # Рейтинг
    activity_score = Column(Integer, default=0, comment="Балл активности")
    period_rank = Column(Integer, nullable=True, comment="Ранг за период")
    
    # Связи
    user = relationship("User", back_populates="user_activities")


class ActivitySummary(BaseModel):
    """
    Модель для сводки активности за период.
    
    Общая статистика чата за определенный период
    для анализа динамики и трендов.
    """
    __tablename__ = "activity_summaries"

    # Период
    period_type = Column(SQLEnum(ActivityPeriod), nullable=False, comment="Тип периода")
    period_date = Column(Date, nullable=False, comment="Дата периода")
    
    # Общая статистика
    total_users = Column(Integer, default=0, comment="Всего активных пользователей")
    total_messages = Column(Integer, default=0, comment="Всего сообщений")
    total_characters = Column(Integer, default=0, comment="Всего символов")
    
    # Топ пользователи (JSON)
    top_users = Column(Text, nullable=True, comment="JSON с топом пользователей")
    activity_distribution = Column(Text, nullable=True, comment="JSON с распределением активности")
    
    # Тренды
    growth_rate = Column(Integer, default=0, comment="Рост активности в %")
    new_active_users = Column(Integer, default=0, comment="Новые активные пользователи")
    
    # Качественные показатели
    average_message_length = Column(Integer, default=0, comment="Средняя длина сообщения")
    engagement_rate = Column(Integer, default=0, comment="Процент вовлеченности")


class WeeklyReport(BaseModel):
    """
    Модель для еженедельных отчетов активности.
    
    Формализованный отчет для публикации в чате
    с топом активных пользователей.
    """
    __tablename__ = "weekly_reports"

    # Период отчета
    week_start_date = Column(Date, nullable=False, comment="Начало недели")
    week_end_date = Column(Date, nullable=False, comment="Конец недели")
    
    # Топ пользователи
    top_active_users = Column(Text, nullable=False, comment="JSON с топом активных")
    connecting_users = Column(Text, nullable=True, comment="JSON с подключающимися")
    
    # Статистика
    total_participants = Column(Integer, default=0, comment="Всего участников")
    active_participants = Column(Integer, default=0, comment="Активных участников")
    activity_percentage = Column(Integer, default=0, comment="Процент активности")
    
    # Сообщение для публикации
    report_message = Column(Text, nullable=False, comment="Готовое сообщение для отправки")
    
    # Статус
    is_published = Column(Boolean, default=False, comment="Опубликован ли отчет")
    published_at = Column(DateTime, nullable=True, comment="Время публикации")
    message_id = Column(Integer, nullable=True, comment="ID сообщения в чате")

