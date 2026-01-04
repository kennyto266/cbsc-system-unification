"""
Strategy ORM Models

Database models for strategy management, parameters, performance, and signals.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, Index, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import sqlalchemy

from .base import BaseModel


class Strategy(BaseModel):
    """Strategy ORM model"""
    __tablename__ = "strategies"

    # Core fields
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # CBSC, Technical, etc.
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # Metadata
    version = Column(Integer, default=1, nullable=False)
    tags = Column(JSON)  # List of tags for categorization
    config = Column(JSON)  # Strategy configuration

    # Relationships
    creator = relationship("User", back_populates="strategies")
    parameters = relationship(
        "StrategyParameter",
        back_populates="strategy",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    performances = relationship(
        "StrategyPerformance",
        back_populates="strategy",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    signals = relationship(
        "StrategySignal",
        back_populates="strategy",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Constraints and indexes
    __table_args__ = (
        Index('idx_strategy_type_active', 'strategy_type', 'is_active'),
        Index('idx_strategy_creator_created', 'creator_id', 'created_at'),
        Index('idx_strategy_public_active', 'is_public', 'is_active'),
        CheckConstraint('length(name) >= 1', name='ck_strategy_name_not_empty'),
        CheckConstraint('length(strategy_type) >= 1', name='ck_strategy_type_not_empty'),
    )

    def add_parameter(self, name: str, value: str, param_type: str):
        """Add a parameter to the strategy"""
        param = StrategyParameter(
            strategy_id=self.id,
            parameter_name=name,
            parameter_value=value,
            parameter_type=param_type
        )
        return param

    def get_active_parameters(self):
        """Get all active (optimized) parameters"""
        return self.parameters.filter(StrategyParameter.is_optimized == True).all()

    def latest_performance(self):
        """Get the most recent performance record"""
        return self.performances.order_by(
            StrategyPerformance.date.desc()
        ).first()

    def recent_signals(self, limit: int = 10):
        """Get recent trading signals"""
        return self.signals.order_by(
            StrategySignal.timestamp.desc()
        ).limit(limit).all()

    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"


class StrategyParameter(BaseModel):
    """Strategy Parameter ORM model"""
    __tablename__ = "strategy_parameters"

    # Core fields
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    parameter_name = Column(String(50), nullable=False)
    parameter_value = Column(String(200), nullable=False)
    parameter_type = Column(String(20), nullable=False)  # int, float, str, bool
    is_optimized = Column(Boolean, default=False, nullable=False)

    # Optimization metadata
    optimization_score = Column(Float)  # Score from parameter optimization
    optimization_date = Column(DateTime(timezone=True))

    # Validation constraints
    min_value = Column(Float)
    max_value = Column(Float)
    allowed_values = Column(JSON)  # List of allowed values for enum-like parameters

    # Relationships
    strategy = relationship("Strategy", back_populates="parameters")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_param_strategy_name', 'strategy_id', 'parameter_name'),
        Index('idx_param_optimized', 'is_optimized'),
        CheckConstraint('parameter_type IN ("int", "float", "str", "bool")', name='ck_param_type'),
    )

    @property
    def typed_value(self):
        """Get parameter value converted to its type"""
        if self.parameter_type == "int":
            return int(self.parameter_value)
        elif self.parameter_type == "float":
            return float(self.parameter_value)
        elif self.parameter_type == "bool":
            return self.parameter_value.lower() in ("true", "1", "yes")
        return self.parameter_value

    def validate_value(self) -> bool:
        """Validate parameter value against constraints"""
        try:
            value = self.typed_value
        except (ValueError, TypeError):
            return False

        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        if self.allowed_values is not None and value not in self.allowed_values:
            return False
        return True

    def __repr__(self):
        return f"<StrategyParameter(name='{self.parameter_name}', value='{self.parameter_value}', type='{self.parameter_type}')>"


class StrategyPerformance(BaseModel):
    """Strategy Performance ORM model"""
    __tablename__ = "strategy_performances"

    # Core fields
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    backtest_id = Column(String(50), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False)

    # Return metrics
    total_return = Column(Float, nullable=False)
    cumulative_return = Column(Float, nullable=False)
    daily_return = Column(Float)

    # Risk metrics
    sharpe_ratio = Column(Float, nullable=False)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    var_95 = Column(Float, nullable=False)  # 95% Value at Risk
    cvar_95 = Column(Float, nullable=False)  # 95% Conditional VaR

    # Trading metrics
    win_rate = Column(Float, nullable=False)
    profit_factor = Column(Float, nullable=False)
    calmar_ratio = Column(Float, nullable=False)
    total_trades = Column(Integer)

    # Additional metrics
    hit_rate = Column(Float)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    best_trade = Column(Float)
    worst_trade = Column(Float)

    # Metadata
    metadata = Column(JSON)  # Additional performance data

    # Relationships
    strategy = relationship("Strategy", back_populates="performances")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_perf_strategy_date', 'strategy_id', 'date'),
        Index('idx_perf_backtest_sharpe', 'backtest_id', 'sharpe_ratio'),
        Index('idx_perf_return', 'total_return'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 1', name='ck_win_rate_range'),
    )

    @property
    def is_profitable(self) -> bool:
        """Check if performance is profitable"""
        return self.total_return > 0

    @property
    def risk_adjusted_return(self) -> float:
        """Calculate risk-adjusted return (return/volatility)"""
        if self.volatility and self.volatility > 0:
            return self.total_return / self.volatility
        return 0

    def __repr__(self):
        return f"<StrategyPerformance(strategy_id={self.strategy_id}, return={self.total_return:.2%}, sharpe={self.sharpe_ratio:.2f})>"


class StrategySignal(BaseModel):
    """Strategy Signal ORM model"""
    __tablename__ = "strategy_signals"

    # Core fields
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # Signal details
    signal_type = Column(String(20), nullable=False)  # buy, sell, hold
    signal_strength = Column(Float, nullable=False)   # 0-100
    confidence = Column(Float, nullable=False)        # 0-100

    # Market context
    symbol = Column(String(10), nullable=False)
    price_at_signal = Column(Float, nullable=False)

    # Context data
    market_data = Column(JSONB)  # Market data snapshot
    parameters_used = Column(JSONB)  # Parameters snapshot when signal was generated

    # Signal execution
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime(timezone=True))
    execution_price = Column(Float)

    # Signal outcome
    outcome = Column(String(20))  # success, failed, pending
    outcome_return = Column(Float)
    outcome_notes = Column(Text)

    # Relationships
    strategy = relationship("Strategy", back_populates="signals")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_signal_strategy_timestamp', 'strategy_id', 'timestamp'),
        Index('idx_signal_type_timestamp', 'signal_type', 'timestamp'),
        Index('idx_signal_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_signal_executed', 'is_executed'),
        CheckConstraint('signal_type IN ("buy", "sell", "hold")', name='ck_signal_type'),
        CheckConstraint('signal_strength >= 0 AND signal_strength <= 100', name='ck_signal_strength'),
        CheckConstraint('confidence >= 0 AND confidence <= 100', name='ck_confidence'),
    )

    @property
    def is_valid(self) -> bool:
        """Check if signal is still valid (not expired)"""
        from datetime import timedelta
        expiry_time = self.timestamp + timedelta(hours=24)
        return datetime.now(timezone.utc) < expiry_time

    @property
    def age_hours(self) -> float:
        """Get signal age in hours"""
        return (datetime.now(timezone.utc) - self.timestamp).total_seconds() / 3600

    def execute(self, price: float):
        """Mark signal as executed"""
        self.is_executed = True
        self.executed_at = datetime.now(timezone.utc)
        self.execution_price = price

    def __repr__(self):
        return f"<StrategySignal(type='{self.signal_type}', symbol='{self.symbol}', strength={self.signal_strength})>"
