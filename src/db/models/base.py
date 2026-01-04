"""
Base ORM Model Definitions

Common base classes and mixins for database models.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

import sqlalchemy
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr


Base = declarative_base()


class TableNameMixin:
    """Mixin for dynamic table name generation"""

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin for timestamp fields (created_at, updated_at)"""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key"""

    @declared_attr
    def id(cls):
        return Column(
            "id",
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            nullable=False
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)

    def soft_delete(self, user_id: Optional[str] = None):
        """Mark record as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id

    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


class BaseModel(TableNameMixin, TimestampMixin, UUIDMixin, Base):
    """Base model class with common fields"""

    __abstract__ = True

    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict, exclude: set = None):
        """Update model from dictionary"""
        exclude = exclude or {'id', 'created_at'}
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self):
        """String representation of model"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
