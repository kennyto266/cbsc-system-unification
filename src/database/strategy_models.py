"""
SQLAlchemy database models for strategy management
策略管理數據庫SQLAlchemy模型
"""

from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Numeric, DateTime,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Mixin for timestamp fields
class TimestampMixin:
    """Mixin for common timestamp fields"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)

# Strategy Category Model
class StrategyCategory(Base, TimestampMixin):
    """Strategy category model"""
    __tablename__ = "strategy_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("strategy_categories.id"), nullable=True)
    level = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    parent = relationship("StrategyCategory", remote_side=[id])
    children = relationship("StrategyCategory", back_populates="parent")

    # Indexes
    __table_args__ = (
        Index("idx_strategy_categories_parent", "parent_id"),
        Index("idx_strategy_categories_level", "level"),
        Index("idx_strategy_categories_active", "is_active"),
    )

    @validates('level')
    def validate_level(self, key, level):
        """Validate level is positive"""
        if level <= 0:
            raise ValueError('Level must be positive')
        return level

    def __repr__(self):
        return f"<StrategyCategory(id={self.id}, name='{self.name}')>"

# User Model (simplified)
class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_active", "is_active"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

# Strategy Model
class Strategy(Base, TimestampMixin):
    """Strategy model"""
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)
    version_number = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    config_schema = Column(JSON, nullable=True)
    parameters_template = Column(JSON, nullable=True)

    # Relationships
    author = relationship("User", back_populates="strategies")
    configs = relationship("StrategyConfig", back_populates="strategy", cascade="all, delete-orphan")
    backtest_results = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")
    performance_records = relationship("PerformanceRecord", back_populates="strategy", cascade="all, delete-orphan")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_strategies_code", "code"),
        Index("idx_strategies_type", "strategy_type"),
        Index("idx_strategies_active", "is_active", "is_deleted"),
        Index("idx_strategies_author", "author_id"),
        Index("idx_strategies_deleted", "is_deleted"),
        CheckConstraint('max_position_size > 0', name='chk_strategy_position_size'),
        CheckConstraint('version_number >= 1', name='chk_strategy_version'),
    )

    @validates('code')
    def validate_code(self, key, code):
        """Validate strategy code format"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', code):
            raise ValueError('Code must start with letter and contain only alphanumeric characters and underscores')
        return code

    def __repr__(self):
        return f"<Strategy(id={self.id}, code='{self.code}', name='{self.name}')>"

# Update User model with strategies relationship
User.strategies = relationship("Strategy", back_populates="author")

# Strategy Configuration Model
class StrategyConfig(Base, TimestampMixin):
    """Strategy configuration model"""
    __tablename__ = "strategy_configs"

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    custom_parameters = Column(JSON, nullable=False)
    risk_tolerance = Column(String(20), default="medium", nullable=False)
    max_position_size = Column(Numeric(15, 2), default=100000.00, nullable=False)
    stop_loss_percent = Column(Numeric(5, 2), default=5.0, nullable=False)
    take_profit_percent = Column(Numeric(5, 2), nullable=True)
    leverage_ratio = Column(Numeric(5, 2), default=1.0, nullable=False)
    rebalance_frequency = Column(String(20), default="daily", nullable=False)
    min_trade_interval = Column(Integer, default=300, nullable=False)
    max_drawdown_limit = Column(Numeric(5, 2), default=20.0, nullable=False)
    volatility_target = Column(Numeric(5, 2), nullable=True)
    correlation_limit = Column(Numeric(5, 2), default=0.7, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_simulation = Column(Boolean, default=True, nullable=False)
    auto_execute = Column(Boolean, default=False, nullable=False)
    notification_settings = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="configs")
    user = relationship("User", back_populates="strategy_configs")
    backtest_results = relationship("BacktestResult", back_populates="strategy_config")
    performance_records = relationship("PerformanceRecord", back_populates="strategy_config")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_strategy_configs_strategy_user", "strategy_id", "user_id"),
        Index("idx_strategy_configs_user_active", "user_id", "is_active"),
        Index("idx_strategy_configs_risk_tolerance", "risk_tolerance"),
        Index("idx_strategy_configs_deleted", "is_deleted"),
        UniqueConstraint("strategy_id", "user_id", "name", name="uq_strategy_configs_name"),
        CheckConstraint('max_position_size > 0', name='chk_configs_position_size'),
        CheckConstraint('stop_loss_percent >= 0 AND stop_loss_percent <= 100', name='chk_configs_stop_loss'),
        CheckConstraint('leverage_ratio > 0', name='chk_configs_leverage'),
        CheckConstraint('min_trade_interval >= 0', name='chk_configs_interval'),
        CheckConstraint('max_drawdown_limit >= 0 AND max_drawdown_limit <= 100', name='chk_configs_drawdown'),
        CheckConstraint('correlation_limit >= 0 AND correlation_limit <= 1', name='chk_configs_correlation'),
    )

    @validates('custom_parameters')
    def validate_custom_parameters(self, key, params):
        """Validate custom parameters are not empty"""
        if not params or not isinstance(params, dict):
            raise ValueError('Custom parameters must be a non-empty dictionary')
        return params

    def __repr__(self):
        return f"<StrategyConfig(id={self.id}, name='{self.name}', strategy_id='{self.strategy_id}')>"

# Update User model with strategy_configs relationship
User.strategy_configs = relationship("StrategyConfig", back_populates="user")

# Backtest Result Model
class BacktestResult(Base, TimestampMixin):
    """Backtest result model"""
    __tablename__ = "backtest_results"

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    strategy_config_id = Column(String(36), ForeignKey("strategy_configs.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    backtest_type = Column(String(20), default="standard", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(20, 2), nullable=False)
    final_capital = Column(Numeric(20, 2), nullable=False)
    total_return = Column(Numeric(10, 4), nullable=False)
    annualized_return = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=False)
    max_drawdown_duration = Column(Integer, nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    sortino_ratio = Column(Numeric(10, 4), nullable=True)
    calmar_ratio = Column(Numeric(10, 4), nullable=True)
    information_ratio = Column(Numeric(10, 4), nullable=True)
    beta = Column(Numeric(10, 4), nullable=True)
    alpha = Column(Numeric(10, 4), nullable=True)
    tracking_error = Column(Numeric(10, 4), nullable=True)
    volatility = Column(Numeric(10, 4), nullable=True)
    downside_deviation = Column(Numeric(10, 4), nullable=True)
    var_95 = Column(Numeric(10, 4), nullable=True)
    var_99 = Column(Numeric(10, 4), nullable=True)
    expected_shortfall = Column(Numeric(10, 4), nullable=True)
    win_rate = Column(Numeric(5, 4), nullable=False)
    profit_factor = Column(Numeric(10, 4), nullable=True)
    recovery_factor = Column(Numeric(10, 4), nullable=True)
    payoff_ratio = Column(Numeric(10, 4), nullable=True)
    average_win = Column(Numeric(20, 2), nullable=True)
    average_loss = Column(Numeric(20, 2), nullable=True)
    largest_win = Column(Numeric(20, 2), nullable=True)
    largest_loss = Column(Numeric(20, 2), nullable=True)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    average_trade_duration = Column(Numeric(10, 2), nullable=True)
    commission_total = Column(Numeric(20, 2), default=0.0, nullable=False)
    slippage_total = Column(Numeric(20, 2), default=0.0, nullable=False)
    benchmark_return = Column(Numeric(10, 4), nullable=True)
    benchmark_volatility = Column(Numeric(10, 4), nullable=True)
    correlation_with_benchmark = Column(Numeric(5, 4), nullable=True)
    monthly_returns = Column(JSON, nullable=True)
    yearly_returns = Column(JSON, nullable=True)
    rolling_returns = Column(JSON, nullable=True)
    trade_distribution = Column(JSON, nullable=True)
    risk_metrics = Column(JSON, nullable=True)
    performance_attribution = Column(JSON, nullable=True)
    sector_allocation = Column(JSON, nullable=True)
    regional_allocation = Column(JSON, nullable=True)
    scenarios_tested = Column(JSON, nullable=True)
    stress_test_results = Column(JSON, nullable=True)
    monte_carlo_results = Column(JSON, nullable=True)
    status = Column(String(20), default="completed", nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)
    data_points_analyzed = Column(Integer, nullable=True)
    parameters_used = Column(JSON, nullable=True)
    market_conditions = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtest_results")
    strategy_config = relationship("StrategyConfig", back_populates="backtest_results")
    user = relationship("User", back_populates="backtest_results")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_backtest_results_strategy", "strategy_id"),
        Index("idx_backtest_results_user", "user_id"),
        Index("idx_backtest_results_date_range", "start_date", "end_date"),
        Index("idx_backtest_results_type", "backtest_type"),
        Index("idx_backtest_results_return", "total_return"),
        Index("idx_backtest_results_sharpe", "sharpe_ratio"),
        Index("idx_backtest_results_deleted", "is_deleted"),
        CheckConstraint('initial_capital > 0', name='chk_backtest_initial_capital'),
        CheckConstraint('final_capital >= 0', name='chk_backtest_final_capital'),
        CheckConstraint('max_drawdown <= 0', name='chk_backtest_drawdown'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 1', name='chk_backtest_win_rate'),
        CheckConstraint('total_trades >= 0', name='chk_backtest_total_trades'),
        CheckConstraint('winning_trades >= 0 AND losing_trades >= 0', name='chk_backtest_trade_counts'),
    )

    def __repr__(self):
        return f"<BacktestResult(id={self.id}, name='{self.name}', strategy_id='{self.strategy_id}')>"

# Update User model with backtest_results relationship
User.backtest_results = relationship("BacktestResult", back_populates="user")

# Performance Record Model
class PerformanceRecord(Base, TimestampMixin):
    """Performance record model"""
    __tablename__ = "performance_records"

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    strategy_config_id = Column(String(36), ForeignKey("strategy_configs.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    record_date = Column(Date, nullable=False)
    record_time = Column(DateTime(timezone=True), nullable=False)
    portfolio_value = Column(Numeric(20, 2), nullable=False)
    cash_balance = Column(Numeric(20, 2), nullable=False)
    invested_value = Column(Numeric(20, 2), nullable=False)
    daily_return = Column(Numeric(10, 4), nullable=False)
    daily_return_pct = Column(Numeric(10, 4), nullable=False)
    cumulative_return = Column(Numeric(10, 4), nullable=False)
    cumulative_return_pct = Column(Numeric(10, 4), nullable=False)
    running_max_drawdown = Column(Numeric(10, 4), nullable=False)
    running_sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    running_volatility = Column(Numeric(10, 4), nullable=True)
    running_var = Column(Numeric(10, 4), nullable=True)
    positions_count = Column(Integer, nullable=False)
    active_positions = Column(Integer, nullable=False)
    long_positions = Column(Integer, nullable=False)
    short_positions = Column(Integer, nullable=False)
    sector_exposure = Column(JSON, nullable=True)
    country_exposure = Column(JSON, nullable=True)
    currency_exposure = Column(JSON, nullable=True)
    risk_metrics = Column(JSON, nullable=True)
    greeks = Column(JSON, nullable=True)
    correlation_matrix = Column(JSON, nullable=True)
    beta_portfolio = Column(Numeric(10, 4), nullable=True)
    tracking_error = Column(Numeric(10, 4), nullable=True)
    information_ratio = Column(Numeric(10, 4), nullable=True)
    turnover_rate = Column(Numeric(10, 4), nullable=True)
    trading_volume = Column(Numeric(20, 2), nullable=False)
    commissions = Column(Numeric(20, 2), default=0.0, nullable=False)
    slippage = Column(Numeric(20, 2), default=0.0, nullable=False)
    margin_used = Column(Numeric(20, 2), default=0.0, nullable=False)
    margin_available = Column(Numeric(20, 2), nullable=True)
    leverage_ratio = Column(Numeric(10, 4), default=1.0, nullable=False)
    risk_score = Column(Numeric(5, 4), nullable=True)
    performance_score = Column(Numeric(5, 4), nullable=True)
    efficiency_score = Column(Numeric(5, 4), nullable=True)
    alerts_triggered = Column(JSON, nullable=True)
    benchmark_comparison = Column(JSON, nullable=True)
    market_conditions = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(36), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="performance_records")
    strategy_config = relationship("StrategyConfig", back_populates="performance_records")
    user = relationship("User", back_populates="performance_records")

    # Indexes and Constraints
    __table_args__ = (
        Index("idx_performance_records_strategy_date", "strategy_id", "record_date"),
        Index("idx_performance_records_config_date", "strategy_config_id", "record_date"),
        Index("idx_performance_records_user_date", "user_id", "record_date"),
        Index("idx_performance_records_date_time", "record_date", "record_time"),
        Index("idx_performance_records_deleted", "is_deleted"),
        UniqueConstraint("strategy_id", "strategy_config_id", "record_date", "record_time", name="uq_performance_record_time"),
        CheckConstraint('portfolio_value >= 0 AND cash_balance >= 0 AND invested_value >= 0', name='chk_performance_values'),
        CheckConstraint('positions_count >= 0 AND active_positions >= 0', name='chk_performance_positions'),
        CheckConstraint('leverage_ratio >= 0', name='chk_performance_leverage'),
    )

    def __repr__(self):
        return f"<PerformanceRecord(id={self.id}, strategy_id='{self.strategy_id}', record_date='{self.record_date}')>"

# Update User model with performance_records relationship
User.performance_records = relationship("PerformanceRecord", back_populates="user")