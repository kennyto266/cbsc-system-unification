"""
Risk Management Models v2.0
Enhanced risk monitoring models compatible with new architecture
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Import base model
from .database import Base


class RiskAlertLevel(str, Enum):
    """Risk alert level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskAlertType(str, Enum):
    """Risk alert type enumeration"""
    VAR_BREACH = "var_breach"
    DRAWDOWN_BREACH = "drawdown_breach"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_RISK = "liquidity_risk"
    CONCENTRATION_RISK = "concentration_risk"
    POSITION_LIMIT = "position_limit"
    SYSTEM_ERROR = "system_error"


class RiskMetricType(str, Enum):
    """Risk metric type enumeration"""
    VALUE_AT_RISK = "value_at_risk"
    EXPECTED_SHORTFALL = "expected_shortfall"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    BETA = "beta"
    CORRELATION = "correlation"
    CONCENTRATION = "concentration"


class RiskMonitoring(Base):
    """Risk monitoring configuration and status"""
    __tablename__ = "risk_monitoring"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False, unique=True)

    # Configuration
    config = Column(JSONB)  # Risk configuration parameters
    alert_config = Column(JSONB)  # Alert thresholds and settings

    # Status
    is_active = Column(Boolean, default=False)
    monitoring_started_at = Column(DateTime)
    monitoring_stopped_at = Column(DateTime)
    last_update = Column(DateTime)

    # Statistics
    total_calculations = Column(Integer, default=0)
    total_alerts_generated = Column(Integer, default=0)
    average_calculation_time = Column(Float)  # in seconds

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    strategy_instance = relationship("StrategyInstance", back_populates="risk_monitoring")
    creator = relationship("User")
    risk_metrics = relationship("RiskMetric", back_populates="monitoring", cascade="all, delete-orphan")
    risk_alerts = relationship("RiskAlert", back_populates="monitoring", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_risk_monitoring_instance', 'strategy_instance_id'),
        Index('idx_risk_monitoring_active', 'is_active'),
        Index('idx_risk_monitoring_created', 'created_at'),
    )


class RiskMetric(Base):
    """Risk metric snapshot"""
    __tablename__ = "risk_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_id = Column(UUID(as_uuid=True), ForeignKey("risk_monitoring.id"), nullable=False)

    # Metric details
    metric_type = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(15, 6))

    # Calculation details
    confidence_level = Column(Numeric(5, 4))  # For VaR/ES (e.g., 0.95)
    window_days = Column(Integer)  # For rolling metrics
    calculation_method = Column(String(50))  # historical, parametric, monte_carlo

    # Additional parameters
    parameters = Column(JSONB)  # Calculation parameters
    benchmark_value = Column(Numeric(15, 6))  # For comparison
    percentile = Column(Numeric(5, 4))  # Percentile in distribution

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
    data_as_of = Column(DateTime)  # Timestamp of underlying data

    # Relationships
    monitoring = relationship("RiskMonitoring", back_populates="risk_metrics")

    __table_args__ = (
        Index('idx_risk_metric_monitoring', 'monitoring_id'),
        Index('idx_risk_metric_type', 'metric_type'),
        Index('idx_risk_metric_calculated', 'calculated_at'),
        Index('idx_risk_metric_composite', 'monitoring_id', 'metric_type', 'calculated_at'),
    )


class RiskAlert(Base):
    """Risk alert record"""
    __tablename__ = "risk_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_id = Column(UUID(as_uuid=True), ForeignKey("risk_monitoring.id"), nullable=False)

    # Alert details
    alert_level = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Trigger conditions
    metric_name = Column(String(100))  # Metric that triggered alert
    threshold_value = Column(Numeric(15, 6))
    actual_value = Column(Numeric(15, 6))
    deviation_percent = Column(Numeric(8, 4))

    # Alert status
    is_active = Column(Boolean, default=True, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)

    # Metadata
    context = Column(JSONB)  # Additional context data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    monitoring = relationship("RiskMonitoring", back_populates="risk_alerts")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])

    __table_args__ = (
        Index('idx_risk_alert_monitoring', 'monitoring_id'),
        Index('idx_risk_alert_level', 'alert_level'),
        Index('idx_risk_alert_type', 'alert_type'),
        Index('idx_risk_alert_active', 'is_active'),
        Index('idx_risk_alert_created', 'created_at'),
        Index('idx_risk_alert_composite', 'monitoring_id', 'is_active', 'created_at'),
    )


class RiskPosition(Base):
    """Position tracking for risk monitoring"""
    __tablename__ = "risk_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)

    # Position details
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20))  # equity, bond, commodity, fx, crypto
    exchange = Column(String(20))

    # Quantities and values
    quantity = Column(Numeric(20, 8))
    avg_cost_price = Column(Numeric(15, 6))
    current_price = Column(Numeric(15, 6))
    market_value = Column(Numeric(20, 6))
    unrealized_pnl = Column(Numeric(20, 6))
    unrealized_pnl_percent = Column(Numeric(8, 4))

    # Risk metrics
    position_weight = Column(Numeric(8, 6))  # Weight in portfolio
    daily_var = Column(Numeric(15, 6))
    beta = Column(Numeric(8, 6))
    volatility = Column(Numeric(8, 6))

    # Limits
    position_limit = Column(Numeric(20, 6))
    weight_limit = Column(Numeric(8, 6))

    # Timestamps
    opened_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Metadata
    sector = Column(String(50))
    country = Column(String(10))
    currency = Column(String(10))
    attributes = Column(JSONB)  # Additional position attributes

    # Relationships
    strategy_instance = relationship("StrategyInstance")

    __table_args__ = (
        Index('idx_risk_position_instance', 'strategy_instance_id'),
        Index('idx_risk_position_symbol', 'symbol'),
        Index('idx_risk_position_asset_type', 'asset_type'),
        Index('idx_risk_position_updated', 'last_updated'),
        Index('idx_risk_position_composite', 'strategy_instance_id', 'symbol'),
    )


class RiskReport(Base):
    """Generated risk reports"""
    __tablename__ = "risk_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)

    # Report details
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    report_format = Column(String(20), nullable=False)  # json, pdf, csv
    title = Column(String(200), nullable=False)

    # Report period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Report content
    summary = Column(JSONB)  # Executive summary
    metrics_snapshot = Column(JSONB)  # Risk metrics at report time
    analysis = Column(JSONB)  # Detailed analysis
    recommendations = Column(JSONB)  # Risk recommendations

    # Performance metrics
    portfolio_return = Column(Numeric(10, 4))
    max_drawdown = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    var_95 = Column(Numeric(10, 4))

    # Report status
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    download_url = Column(String(500))
    file_size = Column(Integer)  # in bytes

    # Metadata
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    strategy_instance = relationship("StrategyInstance")
    generator = relationship("User", foreign_keys=[generated_by])

    __table_args__ = (
        Index('idx_risk_report_instance', 'strategy_instance_id'),
        Index('idx_risk_report_type', 'report_type'),
        Index('idx_risk_report_period', 'period_start', 'period_end'),
        Index('idx_risk_report_created', 'created_at'),
    )


class RiskThreshold(Base):
    """Custom risk thresholds"""
    __tablename__ = "risk_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"))

    # Threshold details
    name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)
    description = Column(Text)

    # Threshold values
    warning_threshold = Column(Numeric(15, 6))
    error_threshold = Column(Numeric(15, 6))
    critical_threshold = Column(Numeric(15, 6))

    # Configuration
    comparison_operator = Column(String(20), default="greater_than")  # greater_than, less_than
    cooldown_period = Column(Integer, default=300)  # seconds
    enabled = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    strategy_instance = relationship("StrategyInstance")

    __table_args__ = (
        Index('idx_risk_threshold_user', 'user_id'),
        Index('idx_risk_threshold_instance', 'strategy_instance_id'),
        Index('idx_risk_threshold_metric', 'metric_type'),
        Index('idx_risk_threshold_enabled', 'enabled'),
    )


class RiskSubscription(Base):
    """WebSocket subscriptions for real-time risk updates"""
    __tablename__ = "risk_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)

    # Subscription details
    connection_id = Column(String(100), nullable=False)
    subscription_types = Column(JSONB)  # ["metrics", "alerts", "positions"]

    # Status
    is_active = Column(Boolean, default=True)
    last_ping = Column(DateTime, default=datetime.utcnow)

    # Metadata
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime)
    client_info = Column(JSONB)  # User agent, IP address, etc.

    # Relationships
    user = relationship("User")
    strategy_instance = relationship("StrategyInstance")

    __table_args__ = (
        Index('idx_risk_subscription_user', 'user_id'),
        Index('idx_risk_subscription_instance', 'strategy_instance_id'),
        Index('idx_risk_subscription_connection', 'connection_id'),
        Index('idx_risk_subscription_active', 'is_active'),
    )