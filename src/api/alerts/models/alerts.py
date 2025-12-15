"""
Alert and notification models
"""
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
import json


class AlertType(str, Enum):
    """Types of alerts"""
    THRESHOLD = "threshold"
    EVENT = "event"
    CUSTOM = "custom"
    SCHEDULED = "scheduled"


class AlertSeverity(str, Enum):
    """Severity levels for alerts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    BROWSER_PUSH = "browser_push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Status of notifications"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AlertCondition(BaseModel):
    """Alert condition configuration"""
    metric: str = Field(..., description="Metric to monitor (e.g., 'drawdown', 'return', 'volatility')")
    operator: str = Field(..., description="Comparison operator (gt, lt, gte, lte, eq)")
    threshold: float = Field(..., description="Threshold value")
    time_window: Optional[int] = Field(None, description="Time window in minutes")

    class Config:
        schema_extra = {
            "example": {
                "metric": "drawdown",
                "operator": "lt",
                "threshold": -0.1,
                "time_window": 60
            }
        }


class AlertRule(BaseModel):
    """Alert rule definition"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    user_id: int
    strategy_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    alert_type: AlertType
    conditions: List[AlertCondition]
    severity: AlertSeverity

    # Configuration
    enabled: bool = True
    cooldown_minutes: int = Field(default=60, description="Cooldown period between alerts")

    # Notification settings
    notification_channels: List[NotificationType]
    notification_template: Optional[str] = None

    # Scheduling (for scheduled alerts)
    schedule_cron: Optional[str] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    class Config:
        from_attributes = True


class Alert(BaseModel):
    """Individual alert instance"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    rule_id: UUID
    rule_name: str
    user_id: int
    strategy_id: Optional[str]
    severity: AlertSeverity

    # Alert data
    title: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Status
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Notification(BaseModel):
    """Notification record"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    alert_id: UUID
    user_id: int

    # Content
    type: NotificationType
    title: str
    content: str

    # Delivery
    recipient: str  # Email address, phone number, device token, etc.
    status: NotificationStatus = NotificationStatus.PENDING

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationPreferences(BaseModel):
    """User notification preferences"""
    user_id: int
    channels: Dict[NotificationType, bool] = Field(
        default_factory=lambda: {
            NotificationType.EMAIL: True,
            NotificationType.BROWSER_PUSH: True,
            NotificationType.IN_APP: True,
            NotificationType.SMS: False,
            NotificationType.WEBHOOK: False
        }
    )

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: time = Field(default=time(22, 0))  # 10 PM
    quiet_hours_end: time = Field(default=time(8, 0))   # 8 AM

    # Frequency settings
    max_notifications_per_hour: int = 10
    max_notifications_per_day: int = 100

    # Content preferences
    email_template: Optional[str] = None
    language: str = "en"

    class Config:
        from_attributes = True


# Database Models (SQLAlchemy)
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AlertRuleDB(Base):
    __tablename__ = "alert_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(String, nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    conditions = Column(JSON, nullable=False)  # List[AlertCondition]
    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Configuration
    enabled = Column(Boolean, default=True)
    cooldown_minutes = Column(Integer, default=60)

    # Notification settings
    notification_channels = Column(JSON, nullable=False)
    notification_template = Column(String)
    schedule_cron = Column(String)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    # Relationships
    alerts = relationship("AlertDB", back_populates="rule")


class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(PG_UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(String)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Alert data
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, default={})

    # Status
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # Relationships
    rule = relationship("AlertRuleDB", back_populates="alerts")
    notifications = relationship("NotificationDB", back_populates="alert")


class NotificationDB(Base):
    __tablename__ = "notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_id = Column(PG_UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Delivery
    recipient = Column(String, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)

    # Metadata
    metadata = Column(JSON, default={})
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)

    # Relationships
    alert = relationship("AlertDB", back_populates="notifications")


class NotificationPreferencesDB(Base):
    __tablename__ = "notification_preferences"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    channels = Column(JSON, nullable=False)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String, default="22:00")
    quiet_hours_end = Column(String, default="08:00")
    max_notifications_per_hour = Column(Integer, default=10)
    max_notifications_per_day = Column(Integer, default=100)
    email_template = Column(String)
    language = Column(String, default="en")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)