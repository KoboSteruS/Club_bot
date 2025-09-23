"""
Базовая модель для ClubBot.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func

from app.core.database import Base


class BaseModel(Base):
    """Базовая модель для всех сущностей ClubBot."""
    
    __abstract__ = True
    
    # Для SQLite используем String вместо UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"
