"""
Backtest Models v2.0
Enhanced backtest models compatible with new architecture
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Import base model
from .database import Base


class BacktestStatus(str, Enum):
    """Backtest status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestMode(str, Enum):
    """Backtest execution modes"""
    STANDARD = "standard"
    RISK_MANAGED = "risk_managed"
    STRESS_TEST = "stress_test"
    MONTE_CARLO = "monte_carlo"
    OPTIMIZATION = "optimization"


class Backtest(Base):
    """Backtest configuration and results model"""
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # References
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=True)

    # Configuration
    symbols = Column(JSONB, nullable=False)  # List of symbols
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    initial_capital = Column(Numeric(15, 2), default=100000.00)
    parameters = Column(JSONB)  # Strategy parameters
    optimization_config = Column(JSONB)  # Optimization parameters if applicable
    risk_config = Column(JSONB)  # Risk management configuration

    # Execution settings
    commission_rate = Column(Numeric(8, 6), default=0.001)  # Commission rate
    slippage_rate = Column(Numeric(8, 6), default=0.0005)  # Slippage rate
    data_source = Column(String(50), default="yahoo")  # Data source
    market_hours_only = Column(Boolean, default=True)  # Trade only during market hours

    # Status and execution
    status = Column(String(20), default=BacktestStatus.PENDING, index=True)
    mode = Column(String(20), default=BacktestMode.STANDARD)
    priority = Column(Integer, default=1)  # Execution priority

    # Results - Performance metrics
    final_equity = Column(Numeric(15, 2))
    total_return = Column(Numeric(10, 4))
    annualized_return = Column(Numeric(10, 4))
    volatility = Column(Numeric(10, 4))
    max_drawdown = Column(Numeric(10, 4))
    calmar_ratio = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    sortino_ratio = Column(Numeric(8, 4))
    information_ratio = Column(Numeric(8, 4))
    beta = Column(Numeric(8, 4))
    alpha = Column(Numeric(10, 4))

    # Risk metrics
    var_95 = Column(Numeric(10, 4))
    var_99 = Column(Numeric(10, 4))
    expected_shortfall_95 = Column(Numeric(10, 4))
    expected_shortfall_99 = Column(Numeric(10, 4))
    tail_ratio = Column(Numeric(8, 4))

    # Trading statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 2))
    avg_trade_return = Column(Numeric(10, 4))
    avg_win = Column(Numeric(15, 2))
    avg_loss = Column(Numeric(15, 2))
    profit_factor = Column(Numeric(8, 2))
    recovery_factor = Column(Numeric(8, 2))

    # Trade duration statistics
    avg_trade_duration = Column(Integer)  # Average duration in periods
    max_trade_duration = Column(Integer)
    min_trade_duration = Column(Integer)

    # Execution metrics
    computation_time = Column(Float)  # Computation time in seconds
    memory_usage = Column(Float)  # Peak memory usage in MB
    data_points = Column(Integer)  # Number of data points processed

    # Detailed results (stored as JSON)
    equity_curve = Column(JSONB)  # Daily equity values
    trade_history = Column(JSONB)  # All trades
    monthly_returns = Column(JSONB)  # Monthly performance
    rolling_metrics = Column(JSONB)  # Rolling performance metrics
    position_history = Column(JSONB)  # Position changes over time

    # Benchmark comparison
    benchmark_return = Column(Numeric(10, 4))
    tracking_error = Column(Numeric(10, 4))
    correlation_benchmark = Column(Numeric(8, 4))

    # Stress test results
    stress_test_results = Column(JSONB)  # Results from stress testing
    scenario_analysis = Column(JSONB)  # Scenario-based analysis results

    # Optimization results (if applicable)
    optimization_results = Column(JSONB)  # Parameter optimization results
    best_parameters = Column(JSONB)  # Best parameter set found

    # Metadata
    error_message = Column(Text)
    notes = Column(Text)
    tags = Column(JSONB)  # Categorization tags
    is_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    user = relationship("User", back_populates="backtests")
    instance = relationship("StrategyInstance", back_populates="backtests")

    __table_args__ = (
        Index('idx_backtest_user', 'user_id'),
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_status', 'status'),
        Index('idx_backtest_dates', 'start_date', 'end_date'),
        Index('idx_backtest_created', 'created_at'),
        CheckConstraint('initial_capital > 0', name='check_positive_capital'),
        CheckConstraint('commission_rate >= 0', name='check_positive_commission'),
        CheckConstraint('slippage_rate >= 0', name='check_positive_slippage'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='check_win_rate_range'),
    )


class BacktestComparison(Base):
    """Backtest comparison results"""
    __tablename__ = "backtest_comparisons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Configuration
    backtest_ids = Column(JSONB, nullable=False)  # List of backtest IDs to compare
    comparison_metrics = Column(JSONB)  # Metrics to compare
    benchmark_strategy_id = Column(UUID, ForeignKey("strategies.id"))  # Optional benchmark

    # Results
    ranking = Column(JSONB)  # Backtest rankings
    best_backtest_id = Column(UUID)  # ID of best performing backtest
    composite_score = Column(JSONB)  # Composite scoring results

    # Statistical analysis
    statistical_significance = Column(JSONB)  # Statistical test results
    correlation_matrix = Column(JSONB)  # Correlation between backtests

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    creator = relationship("User")
    benchmark_strategy = relationship("Strategy")


class BacktestTemplate(Base):
    """Backtest template for quick setup"""
    __tablename__ = "backtest_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # e.g., "momentum", "mean_reversion", "multi_asset"

    # Template configuration
    default_parameters = Column(JSONB)
    default_symbols = Column(JSONB)
    default_timeframe = Column(String(10))  # e.g., "1d", "1h", "5m"
    default_capital = Column(Numeric(15, 2), default=100000.00)
    risk_settings = Column(JSONB)

    # Template metadata
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    rating = Column(Numeric(3, 2))
    tags = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    creator = relationship("User")


class BacktestSchedule(Base):
    """Scheduled backtest configuration"""
    __tablename__ = "backtest_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Schedule configuration
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"))
    schedule_type = Column(String(20))  # 'daily', 'weekly', 'monthly'
    schedule_config = Column(JSONB)  # Schedule-specific configuration
    is_active = Column(Boolean, default=True)

    # Backtest parameters
    parameters = Column(JSONB)
    symbols = Column(JSONB)
    time_range_days = Column(Integer, default=30)  # Number of days for each run

    # Execution settings
    priority = Column(Integer, default=1)
    retry_on_failure = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    notification_settings = Column(JSONB)

    # Run history
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_user = relationship("User")
    strategy = relationship("Strategy")


class BacktestResultArchive(Base):
    """Archive of backtest results for long-term storage"""
    __tablename__ = "backtest_result_archive"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"), nullable=False)

    # Compressed results
    compressed_results = Column(JSONB)  # Compressed backtest results
    performance_summary = Column(JSONB)  # Key performance metrics summary

    # Archive metadata
    archive_date = Column(DateTime, default=datetime.utcnow)
    archive_reason = Column(String(50))  # 'cleanup', 'manual', 'system'
    data_size_mb = Column(Float)  # Size of archived data in MB

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    backtest = relationship("Backtest")