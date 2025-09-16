"""
Модель цели пользователя на неделю.

Содержит информацию о еженедельных целях участников клуба.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class GoalStatus(str, Enum):
    """Статусы цели."""
    
    ACTIVE = "active"  # Активная цель
    COMPLETED = "completed"  # Завершенная цель
    CANCELLED = "cancelled"  # Отмененная цель
    PENDING = "pending"  # Ожидается постановка цели


class Goal(BaseModel):
    """Модель цели пользователя на неделю."""
    
    __tablename__ = "goals"
    
    # ID пользователя (связь с таблицей users)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        doc="ID пользователя"
    )
    
    # Номер недели в году
    week_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Номер недели в году"
    )
    
    # Год
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Год"
    )
    
    # Текст цели
    goal_text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Текст цели на неделю"
    )
    
    # Статус цели
    status: Mapped[GoalStatus] = mapped_column(
        String(20),
        default=GoalStatus.PENDING,
        nullable=False,
        doc="Статус цели"
    )
    
    # Дата создания цели
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Когда была создана цель"
    )
    
    # Дата завершения цели
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Когда была завершена цель"
    )
    
    # Связь с пользователем
    user = relationship("User", back_populates="goals")
    
    def __repr__(self) -> str:
        """Строковое представление цели."""
        return f"<Goal(user_id={self.user_id}, week={self.week_number}, year={self.year}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Проверка, активна ли цель."""
        return self.status == GoalStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        """Проверка, завершена ли цель."""
        return self.status == GoalStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Проверка, ожидается ли постановка цели."""
        return self.status == GoalStatus.PENDING
