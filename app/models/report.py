"""
Модель отчета пользователя.

Содержит информацию о ежедневных отчетах участников клуба.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import BigInteger, DateTime, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ReportStatus(str, Enum):
    """Статусы отчета."""
    
    SENT = "sent"  # Отчет отправлен
    SKIPPED = "skipped"  # Не готов делиться
    PENDING = "pending"  # Ожидается отчет
    MISSED = "missed"  # Пропущен


class Report(BaseModel):
    """Модель отчета пользователя."""
    
    __tablename__ = "reports"
    
    # ID пользователя (связь с таблицей users)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        doc="ID пользователя"
    )
    
    # Дата отчета
    report_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Дата, за которую сдается отчет"
    )
    
    # Текст отчета
    text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Текст отчета пользователя"
    )
    
    # Статус отчета
    status: Mapped[ReportStatus] = mapped_column(
        String(20),
        default=ReportStatus.PENDING,
        nullable=False,
        doc="Статус отчета"
    )
    
    # Дата отправки запроса на отчет
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Когда был отправлен запрос на отчет"
    )
    
    # Дата получения отчета
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Когда был получен отчет"
    )
    
    # Связь с пользователем
    user = relationship("User", back_populates="reports")
    
    def __repr__(self) -> str:
        """Строковое представление отчета."""
        return f"<Report(user_id={self.user_id}, date={self.report_date.date()}, status={self.status})>"
    
    @property
    def is_submitted(self) -> bool:
        """Проверка, отправлен ли отчет."""
        return self.status == ReportStatus.SENT
    
    @property
    def is_skipped(self) -> bool:
        """Проверка, пропущен ли отчет."""
        return self.status == ReportStatus.SKIPPED
    
    @property
    def is_pending(self) -> bool:
        """Проверка, ожидается ли отчет."""
        return self.status == ReportStatus.PENDING
    
    @property
    def is_missed(self) -> bool:
        """Проверка, пропущен ли отчет по времени."""
        return self.status == ReportStatus.MISSED
