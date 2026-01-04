"""
Risk Management API v2 - Database Models
=======================================

SQLAlchemy models for risk management data persistence.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()


class RiskMetrics(Base):
    """Risk metrics storage"""
    __tablename__ = "risk_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(String(255), nullable=False, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # VaR metrics
    var_95_historical = Column(Float, nullable=False)
    var_95_parametric = Column(Float, nullable=False)
    var_99_historical = Column(Float, nullable=False)
    var_99_parametric = Column(Float, nullable=False)

    # Expected Shortfall metrics
    es_95_historical = Column(Float, nullable=False)
    es_95_parametric = Column(Float, nullable=False)
    es_99_historical = Column(Float, nullable=False)
    es_99_parametric = Column(Float, nullable=False)

    # Drawdown metrics
    max_drawdown = Column(Float, nullable=False)
    current_drawdown = Column(Float, nullable=False)
    max_drawdown_duration = Column(Integer, nullable=False)
    avg_drawdown = Column(Float, nullable=False)
    recovery_time = Column(Integer, nullable=True)

    # Volatility metrics
    volatility_daily = Column(Float, nullable=False)
    volatility_monthly = Column(Float, nullable=False)
    volatility_annualized = Column(Float, nullable=False)
    volatility_regime = Column(String(50), nullable=False)

    # Correlation metrics
    avg_correlation = Column(Float, nullable=False)
    max_correlation = Column(Float, nullable=False)
    effective_positions = Column(Float, nullable=False)
    concentration_ratio = Column(Float, nullable=False)

    # Performance metrics
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)
    information_ratio = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    tail_ratio = Column(Float, nullable=True)
    skewness = Column(Float, nullable=True)
    excess_kurtosis = Column(Float, nullable=True)

    # Metadata
    calculation_time_ms = Column(Float, nullable=True)
    data_points = Column(Integer, nullable=True)
    confidence_level = Column(Float, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_risk_metrics_portfolio_timestamp', 'portfolio_id', 'timestamp'),
        Index('idx_risk_metrics_strategy_timestamp', 'strategy_id', 'timestamp'),
    )


class AlertConfiguration(Base):
    """Alert configuration storage"""
    __tablename__ = "alert_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    metric_type = Column(String(100), nullable=False)
    portfolio_id = Column(String(255), nullable=True, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)

    # Thresholds
    threshold_warning = Column(Float, nullable=True)
    threshold_error = Column(Float, nullable=True)
    threshold_critical = Column(Float, nullable=True)

    # Configuration
    comparison_operator = Column(String(50), nullable=False, default="greater_than")
    cooldown_period = Column(Integer, nullable=False, default=300)
    enabled = Column(Boolean, nullable=False, default=True)

    # Notification settings
    notification_channels = Column(JSON, nullable=True, default=list)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)


class Alert(Base):
    """Alert storage"""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    configuration_id = Column(UUID(as_uuid=True), ForeignKey("alert_configurations.id"), nullable=False)
    portfolio_id = Column(String(255), nullable=True, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)

    # Alert details
    level = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active", index=True)
    message = Column(Text, nullable=False)
    current_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Action details
    action_taken = Column(Text, nullable=True)
    action_required = Column(Boolean, nullable=False, default=True)

    # Relationships
    configuration = relationship("AlertConfiguration", backref="alerts")

    # Indexes
    __table_args__ = (
        Index('idx_alerts_portfolio_status_created', 'portfolio_id', 'status', 'created_at'),
        Index('idx_alerts_strategy_status_created', 'strategy_id', 'status', 'created_at'),
        Index('idx_alerts_level_created', 'level', 'created_at'),
    )


class RiskReport(Base):
    """Risk report storage"""
    __tablename__ = "risk_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(String(255), nullable=True, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)
    report_type = Column(String(100), nullable=False)

    # Report parameters
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    metrics = Column(JSON, nullable=True, default=list)
    format = Column(String(50), nullable=False, default="json")

    # Report details
    status = Column(String(50), nullable=False, default="pending", index=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    download_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Report content (for JSON format)
    content = Column(JSON, nullable=True)

    # Metadata
    created_by = Column(String(255), nullable=True)
    include_charts = Column(Boolean, nullable=False, default=True)
    include_recommendations = Column(Boolean, nullable=False, default=True)

    # Indexes
    __table_args__ = (
        Index('idx_reports_portfolio_status_created', 'portfolio_id', 'status', 'created_at'),
        Index('idx_reports_strategy_status_created', 'strategy_id', 'status', 'created_at'),
    )


class RiskAdjustment(Base):
    """Risk adjustment storage"""
    __tablename__ = "risk_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(String(255), nullable=False, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)
    request_id = Column(String(255), nullable=False, unique=True, index=True)

    # Adjustment details
    adjustment_type = Column(String(100), nullable=False)
    trigger = Column(JSON, nullable=False)
    adjustments = Column(JSON, nullable=False)

    # Execution details
    execution_status = Column(String(50), nullable=False, default="pending")
    executed_at = Column(DateTime, nullable=True)
    execution_error = Column(Text, nullable=True)

    # Risk metrics before and after
    pre_adjustment_risk = Column(JSON, nullable=True)
    post_adjustment_risk = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Metadata
    created_by = Column(String(255), nullable=True)
    auto_executed = Column(Boolean, nullable=False, default=False)


class RiskRecommendation(Base):
    """Risk recommendation storage"""
    __tablename__ = "risk_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(String(255), nullable=True, index=True)
    strategy_id = Column(String(255), nullable=True, index=True)

    # Recommendation details
    type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False, index=True)
    impact = Column(String(50), nullable=False)
    effort = Column(String(50), nullable=False)

    # Related metrics and actions
    metrics = Column(JSON, nullable=False, default=list)
    actions = Column(JSON, nullable=False, default=list)
    expected_benefit = Column(String(1000), nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")
    acknowledged_at = Column(DateTime, nullable=True)
    implemented_at = Column(DateTime, nullable=True)
    implemented_by = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    created_by = Column(String(255), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_recommendations_portfolio_priority_created', 'portfolio_id', 'priority', 'created_at'),
        Index('idx_recommendations_strategy_priority_created', 'strategy_id', 'priority', 'created_at'),
        Index('idx_recommendations_status_created', 'status', 'created_at'),
    )


class RiskUserPreferences(Base):
    """User risk preferences storage"""
    __tablename__ = "risk_user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, unique=True, index=True)

    # Alert preferences
    alert_email_enabled = Column(Boolean, nullable=False, default=True)
    alert_sms_enabled = Column(Boolean, nullable=False, default=False)
    alert_webhook_enabled = Column(Boolean, nullable=False, default=False)
    alert_webhook_url = Column(String(500), nullable=True)

    # Report preferences
    default_report_format = Column(String(50), nullable=False, default="pdf")
    auto_generate_reports = Column(Boolean, nullable=False, default=False)
    report_frequency = Column(String(50), nullable=True)

    # Dashboard preferences
    default_time_horizon = Column(String(50), nullable=False, default="monthly")
    risk_tolerance = Column(String(50), nullable=False, default="medium")

    # Notification settings
    notification_channels = Column(JSON, nullable=True, default=list)
    quiet_hours_start = Column(String(10), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(10), nullable=True)    # HH:MM format

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskAuditLog(Base):
    """Risk management audit log"""
    __tablename__ = "risk_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)

    # Request details
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Data changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Result
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_audit_user_action_created', 'user_id', 'action', 'created_at'),
        Index('idx_audit_resource_created', 'resource_type', 'resource_id', 'created_at'),
    )