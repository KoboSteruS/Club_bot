"""
Схемы для работы с целями.

Содержит Pydantic модели для валидации данных целей.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.goal import GoalStatus


class GoalBase(BaseModel):
    """Базовая схема цели."""
    
    goal_text: Optional[str] = Field(None, description="Текст цели")
    status: GoalStatus = Field(GoalStatus.PENDING, description="Статус цели")


class GoalCreate(GoalBase):
    """Схема для создания цели."""
    
    user_id: str = Field(..., description="ID пользователя")
    week_number: int = Field(..., description="Номер недели")
    year: int = Field(..., description="Год")


class GoalUpdate(BaseModel):
    """Схема для обновления цели."""
    
    goal_text: Optional[str] = Field(None, description="Текст цели")
    status: Optional[GoalStatus] = Field(None, description="Статус цели")


class GoalResponse(GoalBase):
    """Схема ответа с данными цели."""
    
    id: str = Field(..., description="ID цели")
    user_id: str = Field(..., description="ID пользователя")
    week_number: int = Field(..., description="Номер недели")
    year: int = Field(..., description="Год")
    created_at: Optional[datetime] = Field(None, description="Дата создания")
    completed_at: Optional[datetime] = Field(None, description="Дата завершения")
    
    class Config:
        from_attributes = True
