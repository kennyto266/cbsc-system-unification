"""
Backtest database model (SQLAlchemy).
"""

from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from .base_mixin import TimestampMixin
from typing import Optional, Dict, Any


class Backtest(Base, TimestampMixin):
    """Backtest model"""
    __tablename__ = "backtests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    initial_capital: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )

    # Execution tracking
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None
    )

    # Performance metrics (stored as JSON)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=None
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="backtests")
    strategy: Mapped["Strategy"] = relationship("Strategy", backref="backtests")

    def __repr__(self) -> str:
        return f"<Backtest(id={self.id}, name='{self.name}', status='{self.status}')>"
