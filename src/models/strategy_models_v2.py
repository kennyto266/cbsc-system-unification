"""
Strategy Models v2.0
New strategy management data models for CBSC platform
Phase 3.1 - 實現策略數據模型
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint, CheckConstraint,
    ARRAY, NUMERIC
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, validator, HttpUrl
import uuid

Base = declarative_base()


# Enums
class StrategyType(str, Enum):
    """Strategy type enumeration"""
    TECHNICAL = "technical"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    PORTFOLIO = "portfolio"
    FUNDAMENTAL = "fundamental"
    COMBINATION = "combination"


class StrategyStatus(str, Enum):
    """Strategy status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    TESTING = "testing"


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class TimeFrame(str, Enum):
    """Time frame enumeration"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


# SQLAlchemy Models
class StrategyCategory(Base):
    """Strategy category model"""
    __tablename__ = "strategy_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("strategy_categories.id"))
    icon = Column(String(50))  # Icon name for UI
    color = Column(String(7))  # Hex color code
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    parent = relationship("StrategyCategory", remote_side=[id])
    children = relationship("StrategyCategory", back_populates="parent")
    strategies = relationship("Strategy", back_populates="category")

    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_active', 'is_active'),
    )


class Strategy(Base):
    """Main strategy model"""
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)  # URL-friendly name
    description = Column(Text)
    strategy_type = Column(String(20), nullable=False)  # StrategyType enum
    status = Column(String(20), default=StrategyStatus.DRAFT)  # StrategyStatus enum

    # Category and classification
    category_id = Column(UUID(as_uuid=True), ForeignKey("strategy_categories.id"))
    tags = Column(ARRAY(String))  # Array of tags for classification

    # Configuration
    config = Column(JSONB)  # Strategy configuration parameters
    default_parameters = Column(JSONB)  # Default parameter values
    parameter_schema = Column(JSONB)  # JSON schema for parameter validation

    # Performance and risk
    risk_level = Column(String(20), default=RiskLevel.MEDIUM)  # RiskLevel enum
    expected_return = Column(Float)  # Expected annual return
    max_drawdown = Column(Float)  # Maximum historical drawdown
    sharpe_ratio = Column(Float)  # Sharpe ratio
    win_rate = Column(Float)  # Win rate percentage

    # Trading parameters
    timeframes = Column(ARRAY(String))  # Supported timeframes
    symbols = Column(ARRAY(String))  # Tradable symbols (empty for all)
    exchanges = Column(ARRAY(String))  # Supported exchanges
    min_capital = Column(Float)  # Minimum capital requirement

    # Metadata
    version = Column(String(20), default="1.0.0")
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)  # Public visibility
    is_template = Column(Boolean, default=False)  # Template strategy
    featured = Column(Boolean, default=False)  # Featured in gallery

    # Usage tracking
    usage_count = Column(Integer, default=0)
    rating = Column(Float)  # Average rating
    rating_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime)

    # Relationships
    category = relationship("StrategyCategory", back_populates="strategies")
    author = relationship("User", back_populates="strategies")
    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")
    instances = relationship("StrategyInstance", back_populates="strategy", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    performance_records = relationship("StrategyPerformance", back_populates="strategy", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_strategy_type', 'strategy_type'),
        Index('idx_strategy_status', 'status'),
        Index('idx_strategy_author', 'author_id'),
        Index('idx_strategy_category', 'category_id'),
        Index('idx_strategy_public', 'is_public'),
        Index('idx_strategy_featured', 'featured'),
        Index('idx_strategy_created', 'created_at'),
        Index('idx_strategy_tags', 'tags', postgresql_using='gin'),
        CheckConstraint('expected_return >= -100 AND expected_return <= 1000', name='check_expected_return_range'),
        CheckConstraint('max_drawdown >= 0 AND max_drawdown <= 100', name='check_max_drawdown_range'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='check_win_rate_range'),
        CheckConstraint('rating >= 0 AND rating <= 5', name='check_rating_range'),
    )

    @validates('slug')
    def validate_slug(self, key, slug):
        """Validate slug format"""
        import re
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return slug

    @validates('config')
    def validate_config(self, key, config):
        """Validate configuration JSON"""
        if config is not None and not isinstance(config, dict):
            raise ValueError('Configuration must be a dictionary')
        return config


class StrategyVersion(Base):
    """Strategy version history"""
    __tablename__ = "strategy_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    version = Column(String(20), nullable=False)
    changelog = Column(Text)  # Description of changes
    config = Column(JSONB, nullable=False)  # Complete configuration snapshot
    parameters = Column(JSONB)  # Parameter values for this version

    # Version metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_major = Column(Boolean, default=False)  # Major version (breaking changes)
    is_stable = Column(Boolean, default=False)  # Stable release

    # Performance benchmarking
    benchmark_data = Column(JSONB)  # Benchmark results
    test_results = Column(JSONB)  # Unit test results

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    strategy = relationship("Strategy", back_populates="versions")
    creator = relationship("User")

    __table_args__ = (
        UniqueConstraint('strategy_id', 'version', name='unique_strategy_version'),
        Index('idx_version_strategy', 'strategy_id'),
        Index('idx_version_created', 'created_at'),
    )


class StrategyInstance(Base):
    """Running strategy instances"""
    __tablename__ = "strategy_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)  # Custom instance name

    # Instance configuration
    parameters = Column(JSONB)  # Runtime parameter overrides
    symbols = Column(ARRAY(String))  # Symbols to trade
    capital_allocation = Column(Float)  # Allocated capital
    position_sizing = Column(JSONB)  # Position sizing rules

    # State
    status = Column(String(20), default="stopped")  # stopped, running, paused, error
    last_signal = Column(JSONB)  # Last trading signal
    current_positions = Column(JSONB)  # Current open positions

    # Performance tracking
    start_equity = Column(Float)  # Starting equity
    current_equity = Column(Float)  # Current equity
    total_return = Column(Float)  # Total return
    daily_return = Column(Float)  # Daily return

    # Risk management
    risk_settings = Column(JSONB)  # Risk management settings
    current_drawdown = Column(Float)  # Current drawdown
    var_95 = Column(Float)  # Value at Risk (95%)

    # Execution
    is_paper_trading = Column(Boolean, default=True)  # Paper vs live trading
    auto_trade = Column(Boolean, default=False)  # Automatic trading
    signal_notifications = Column(JSONB)  # Notification settings

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    last_signal_at = Column(DateTime)

    # Relationships
    strategy = relationship("Strategy", back_populates="instances")
    user = relationship("User", back_populates="strategy_instances")
    trades = relationship("Trade", back_populates="instance", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_instance_strategy', 'strategy_id'),
        Index('idx_instance_user', 'user_id'),
        Index('idx_instance_status', 'status'),
        Index('idx_instance_active', 'is_paper_trading', 'auto_trade'),
        CheckConstraint('capital_allocation > 0', name='check_positive_capital'),
    )


class StrategyPerformance(Base):
    """Strategy performance tracking"""
    __tablename__ = "strategy_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # Performance date

    # Return metrics
    daily_return = Column(Float)
    cumulative_return = Column(Float)
    annualized_return = Column(Float)

    # Risk metrics
    volatility = Column(Float)
    max_drawdown = Column(Float)
    current_drawdown = Column(Float)

    # Risk-adjusted returns
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)

    # Benchmark comparison
    benchmark_return = Column(Float)
    alpha = Column(Float)
    beta = Column(Float)
    tracking_error = Column(Float)

    # Trading metrics
    win_rate = Column(Float)
    profit_factor = Column(Float)
    avg_trade_return = Column(Float)
    trade_count = Column(Integer)

    # Portfolio metrics
    equity = Column(Float)
    exposure = Column(Float)
    leverage = Column(Float)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    strategy = relationship("Strategy", back_populates="performance_records")

    __table_args__ = (
        UniqueConstraint('strategy_id', 'date', name='unique_strategy_daily_performance'),
        Index('idx_performance_strategy', 'strategy_id'),
        Index('idx_performance_date', 'date'),
        Index('idx_performance_returns', 'daily_return', 'cumulative_return'),
    )


class Backtest(Base):
    """Backtest results"""
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)

    # Backtest configuration
    parameters = Column(JSONB)  # Strategy parameters used
    symbols = Column(ARRAY(String))  # Symbols tested
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, default=100000)

    # Performance results
    final_equity = Column(Float)
    total_return = Column(Float)
    annualized_return = Column(Float)

    # Risk metrics
    max_drawdown = Column(Float)
    volatility = Column(Float)
    var_95 = Column(Float)  # Value at Risk
    expected_shortfall = Column(Float)

    # Risk-adjusted metrics
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)

    # Trading statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    profit_factor = Column(Float)

    # Benchmark comparison
    benchmark_return = Column(Float)
    alpha = Column(Float)
    beta = Column(Float)
    information_ratio = Column(Float)

    # Detailed results
    equity_curve = Column(JSONB)  # Daily equity values
    trade_history = Column(JSONB)  # All trades
    monthly_returns = Column(JSONB)  # Monthly performance
    rolling_metrics = Column(JSONB)  # Rolling performance metrics

    # Status and metadata
    status = Column(String(20), default="completed")  # running, completed, failed
    error_message = Column(Text)
    computation_time = Column(Float)  # Time in seconds
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    user = relationship("User", back_populates="backtests")

    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_user', 'user_id'),
        Index('idx_backtest_dates', 'start_date', 'end_date'),
        Index('idx_backtest_performance', 'total_return', 'sharpe_ratio'),
        CheckConstraint('initial_capital > 0', name='check_positive_initial_capital'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='check_backtest_win_rate'),
    )


class Trade(Base):
    """Individual trade records"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"))  # Null for live trades

    # Trade details
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # long, short
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)

    # Timestamps
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    duration = Column(Integer)  # Duration in minutes/days

    # Financials
    entry_value = Column(Float)  # Quantity * Entry Price
    exit_value = Column(Float)  # Quantity * Exit Price
    gross_pnl = Column(Float)  # P&L before fees
    fees = Column(Float, default=0)
    net_pnl = Column(Float)  # P&L after fees
    return_pct = Column(Float)  # Return percentage

    # Trade metadata
    exit_reason = Column(String(50))  # stop_loss, take_profit, signal, manual
    signal_confidence = Column(Float)  # Signal confidence (0-1)
    strategy_notes = Column(Text)  # Strategy-specific notes

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    instance = relationship("StrategyInstance", back_populates="trades")
    backtest = relationship("Backtest")

    __table_args__ = (
        Index('idx_trade_instance', 'instance_id'),
        Index('idx_trade_backtest', 'backtest_id'),
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_times', 'entry_time', 'exit_time'),
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
        CheckConstraint('entry_price > 0', name='check_positive_entry_price'),
    )