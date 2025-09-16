"""
Схемы для работы с отчетами.

Содержит Pydantic модели для валидации данных отчетов.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.report import ReportStatus


class ReportBase(BaseModel):
    """Базовая схема отчета."""
    
    text: Optional[str] = Field(None, description="Текст отчета")
    status: ReportStatus = Field(ReportStatus.PENDING, description="Статус отчета")


class ReportCreate(ReportBase):
    """Схема для создания отчета."""
    
    user_id: str = Field(..., description="ID пользователя")
    report_date: datetime = Field(..., description="Дата отчета")


class ReportUpdate(BaseModel):
    """Схема для обновления отчета."""
    
    text: Optional[str] = Field(None, description="Текст отчета")
    status: Optional[ReportStatus] = Field(None, description="Статус отчета")


class ReportResponse(ReportBase):
    """Схема ответа с данными отчета."""
    
    id: str = Field(..., description="ID отчета")
    user_id: str = Field(..., description="ID пользователя")
    report_date: datetime = Field(..., description="Дата отчета")
    requested_at: Optional[datetime] = Field(None, description="Дата запроса")
    submitted_at: Optional[datetime] = Field(None, description="Дата отправки")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    
    class Config:
        from_attributes = True
