"""
CBSC統一數據模型基礎類

定義所有數據模型的基礎結構和通用功能。
"""

from datetime import datetime, timezone
from typing import Optional, Any, Dict
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from pydantic import BaseModel as PydanticBaseModel, Field, validator
import uuid

# SQLAlchemy Base
UnifiedBase = declarative_base()

class TableNameMixin:
    """動態生成表名"""

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class TimestampMixin:
    """時間戳混入類"""

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class UUIDMixin:
    """UUID混入類"""

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)

class AuditMixin:
    """審計混入類"""

    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)

class UnifiedBaseModel(TableNameMixin, TimestampMixin, UUIDMixin, AuditMixin, UnifiedBase):
    """SQLAlchemy統一基礎模型類"""

    __abstract__ = True

    # 通用字段
    version = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    def soft_delete(self, user_id: Optional[str] = None):
        """軟刪除"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    def restore(self):
        """恢復軟刪除"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_metadata(self, key: str, value: Any):
        """更新元數據"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value
        self.updated_at = datetime.now(timezone.utc)

# Pydantic基礎模型
class UnifiedSchema(PydanticBaseModel):
    """Pydantic統一基礎Schema"""

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: Optional[int] = 1
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class BaseResponse(PydanticBaseModel):
    """基礎響應模型"""

    success: bool = True
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Optional[Any] = None
    error: Optional[str] = None

class PaginationParams(PydanticBaseModel):
    """分頁參數"""

    page: int = Field(1, ge=1, description="頁碼")
    page_size: int = Field(20, ge=1, le=100, description="每頁數量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse(PydanticBaseModel):
    """分頁響應模型"""

    items: list
    total: int
    page: int
    page_size: int
    total_pages: int

    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        total = values.get('total', 0)
        page_size = values.get('page_size', 20)
        return (total + page_size - 1) // page_size if total > 0 else 0

# 通用枚舉和常量
class StatusEnum:
    """狀態枚舉"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"
    DELETED = "deleted"

class RiskLevelEnum:
    """風險等級枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

class PriorityEnum:
    """優先級枚舉"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"