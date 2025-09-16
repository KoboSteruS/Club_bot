"""
Модели для системы ритуалов ЯДРА.

Этот модуль содержит модели для управления ритуалами:
- Ritual: Конфигурация ритуалов
- UserRitual: Участие пользователей в ритуалах
- RitualResponse: Ответы пользователей на ритуалы
"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import BaseModel


class RitualType(str, Enum):
    """Тип ритуала."""
    MORNING = "morning"       # Утренний ритуал
    EVENING = "evening"       # Вечерний ритуал
    WEEKLY_CHALLENGE = "weekly_challenge"  # Еженедельный вызов
    WEEKLY_GOALS = "weekly_goals"         # Цели на неделю
    FRIDAY_CYCLE = "friday_cycle"         # Пятничный цикл


class RitualSchedule(str, Enum):
    """Расписание ритуала."""
    DAILY = "daily"           # Ежедневно
    WEEKLY = "weekly"         # Еженедельно
    MONTHLY = "monthly"       # Ежемесячно


class ResponseType(str, Enum):
    """Тип ответа на ритуал."""
    COMPLETED = "completed"   # Выполнено
    SKIPPED = "skipped"      # Пропущено
    PARTIAL = "partial"      # Частично выполнено
    TEXT = "text"            # Текстовый ответ


class Ritual(BaseModel):
    """
    Модель ритуала.
    
    Содержит конфигурацию ритуалов ЯДРА:
    - Время отправки
    - Текст сообщения
    - Доступные кнопки ответа
    """
    __tablename__ = "rituals"

    name = Column(String(200), nullable=False, comment="Название ритуала")
    description = Column(Text, nullable=True, comment="Описание ритуала")
    type = Column(SQLEnum(RitualType), nullable=False, comment="Тип ритуала")
    schedule = Column(SQLEnum(RitualSchedule), nullable=False, comment="Расписание")
    
    # Время отправки
    send_hour = Column(Integer, nullable=False, comment="Час отправки (0-23)")
    send_minute = Column(Integer, default=0, comment="Минута отправки (0-59)")
    weekday = Column(Integer, nullable=True, comment="День недели (0=понедельник, 6=воскресенье)")
    
    # Контент
    message_title = Column(String(500), nullable=False, comment="Заголовок сообщения")
    message_text = Column(Text, nullable=False, comment="Текст сообщения")
    
    # Кнопки ответа (JSON строка с кнопками)
    response_buttons = Column(Text, nullable=True, comment="JSON с кнопками ответа")
    
    # Настройки
    is_active = Column(Boolean, default=True, comment="Активен ли ритуал")
    requires_subscription = Column(Boolean, default=True, comment="Требует ли активную подписку")
    sort_order = Column(Integer, default=0, comment="Порядок сортировки")
    
    # Связи
    user_rituals = relationship("UserRitual", back_populates="ritual", cascade="all, delete-orphan")
    responses = relationship("RitualResponse", back_populates="ritual", cascade="all, delete-orphan")


class UserRitual(BaseModel):
    """
    Модель участия пользователя в ритуале.
    
    Отслеживает, когда пользователь последний раз получал ритуал
    и его общую статистику участия.
    """
    __tablename__ = "user_rituals"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="ID пользователя")
    ritual_id = Column(String(36), ForeignKey("rituals.id"), nullable=False, comment="ID ритуала")
    
    # Статистика
    last_sent_at = Column(DateTime, nullable=True, comment="Когда последний раз отправлен")
    total_sent = Column(Integer, default=0, comment="Всего отправлено")
    total_responses = Column(Integer, default=0, comment="Всего ответов")
    total_completed = Column(Integer, default=0, comment="Всего выполнено")
    total_skipped = Column(Integer, default=0, comment="Всего пропущено")
    
    # Настройки пользователя
    is_enabled = Column(Boolean, default=True, comment="Включен ли ритуал для пользователя")
    timezone_offset = Column(Integer, default=3, comment="Смещение часового пояса")
    
    # Связи
    user = relationship("User", back_populates="user_rituals")
    ritual = relationship("Ritual", back_populates="user_rituals")
    responses = relationship("RitualResponse", back_populates="user_ritual", cascade="all, delete-orphan")


class RitualResponse(BaseModel):
    """
    Модель ответа пользователя на ритуал.
    
    Содержит информацию о том, как пользователь ответил
    на конкретный ритуал.
    """
    __tablename__ = "ritual_responses"

    user_ritual_id = Column(String(36), ForeignKey("user_rituals.id"), nullable=False, comment="ID участия в ритуале")
    ritual_id = Column(String(36), ForeignKey("rituals.id"), nullable=False, comment="ID ритуала")
    
    # Ответ
    response_type = Column(SQLEnum(ResponseType), nullable=False, comment="Тип ответа")
    response_text = Column(Text, nullable=True, comment="Текст ответа (если есть)")
    button_clicked = Column(String(100), nullable=True, comment="Нажатая кнопка")
    
    # Время
    sent_at = Column(DateTime, nullable=False, comment="Когда отправлен ритуал")
    responded_at = Column(DateTime, nullable=True, comment="Когда дан ответ")
    
    # Связи
    user_ritual = relationship("UserRitual", back_populates="responses")
    ritual = relationship("Ritual", back_populates="responses")
