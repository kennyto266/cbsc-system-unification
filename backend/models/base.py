"""
Base model definitions for database tables.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
# Base is imported from core.database to avoid circular dependency
# But we define mixins here that don't depend on Base

__all__ = ["TimestampMixin", "SoftDeleteMixin"]


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None
    )


__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin"]
