"""
Trading Models v2.0
Enhanced trading models compatible with new architecture
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, Numeric, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Import base model
from .database import Base


class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionStatus(str, Enum):
    """Position status enumeration"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CLOSING = "CLOSING"


class TradeStatus(str, Enum):
    """Trade status enumeration"""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class BrokerAccount(Base):
    """Broker account configuration"""
    __tablename__ = "broker_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Broker details
    broker_name = Column(String(50), nullable=False)  # e.g., "futu", "interactive_brokers", "binance"
    account_identifier = Column(String(100), nullable=False)  # Account number or ID
    account_type = Column(String(20), default="simulation")  # simulation, live, paper

    # Connection details
    credentials = Column(JSONB)  # API keys, secrets (encrypted)
    connection_config = Column(JSONB)  # Connection parameters
    trading_permissions = Column(JSONB)  # Trading permissions and limits

    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_connected = Column(DateTime)
    connection_error = Column(Text)

    # Limits and constraints
    daily_loss_limit = Column(Numeric(15, 2))
    position_size_limit = Column(Numeric(15, 2))
    max_leverage = Column(Numeric(8, 4))
    allowed_symbols = Column(JSONB)  # List of allowed trading symbols

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    portfolios = relationship("Portfolio", back_populates="broker_account")
    orders = relationship("Order", back_populates="broker_account")

    __table_args__ = (
        Index('idx_broker_account_user', 'user_id'),
        Index('idx_broker_account_name', 'broker_name'),
        Index('idx_broker_account_active', 'is_active'),
    )


class Portfolio(Base):
    """Portfolio tracking for strategy instances"""
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id"), nullable=False)

    # Capital tracking
    initial_capital = Column(Numeric(15, 2), nullable=False)
    current_capital = Column(Numeric(15, 2))
    allocated_capital = Column(Numeric(15, 2))
    available_capital = Column(Numeric(15, 2))

    # Performance metrics
    total_pnl = Column(Numeric(15, 2))
    total_pnl_percent = Column(Numeric(8, 4))
    unrealized_pnl = Column(Numeric(15, 2))
    realized_pnl = Column(Numeric(15, 2))
    max_drawdown = Column(Numeric(8, 4))
    daily_pnl = Column(Numeric(15, 2))

    # Position summary
    total_positions = Column(Integer, default=0)
    long_positions = Column(Integer, default=0)
    short_positions = Column(Integer, default=0)
    total_exposure = Column(Numeric(15, 2))

    # Trading activity
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Numeric(5, 2))

    # Status and timing
    status = Column(String(20), default="initialized")  # initialized, active, trading, stopped, error
    trading_started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    last_trade_at = Column(DateTime)
    final_capital = Column(Numeric(15, 2))

    # Risk metrics
    var_95 = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    beta = Column(Numeric(8, 4))
    volatility = Column(Numeric(8, 4))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    strategy_instance = relationship("StrategyInstance", back_populates="portfolios")
    broker_account = relationship("BrokerAccount", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio")
    orders = relationship("Order", back_populates="portfolio")

    __table_args__ = (
        Index('idx_portfolio_instance', 'strategy_instance_id'),
        Index('idx_portfolio_broker', 'broker_account_id'),
        Index('idx_portfolio_status', 'status'),
        Index('idx_portfolio_created', 'created_at'),
    )


class Order(Base):
    """Order tracking"""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id"), nullable=False)

    # Order details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    price = Column(Numeric(15, 6))
    stop_price = Column(Numeric(15, 6))

    # Execution details
    status = Column(String(20), default=OrderStatus.PENDING, index=True)
    filled_quantity = Column(Numeric(20, 8), default=0)
    remaining_quantity = Column(Numeric(20, 8))
    average_fill_price = Column(Numeric(15, 6))
    commission = Column(Numeric(15, 6))
    total_cost = Column(Numeric(20, 6))

    # Broker references
    broker_order_id = Column(String(100))
    exchange_order_id = Column(String(100))

    # Timing
    submitted_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Order attributes
    time_in_force = Column(String(10))  # DAY, GTC, IOC, FOK
    is_iceberg = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    parent_order_id = Column(UUID, ForeignKey("orders.id"))

    # Error handling
    error_code = Column(String(50))
    error_message = Column(Text)
    rejection_reason = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    strategy_signal_id = Column(String(100))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="orders")
    broker_account = relationship("BrokerAccount", back_populates="orders")
    child_orders = relationship("Order", remote_side=[id])
    position = relationship("Position", back_populates="orders")

    __table_args__ = (
        Index('idx_order_portfolio', 'portfolio_id'),
        Index('idx_order_symbol', 'symbol'),
        Index('idx_order_status', 'status'),
        Index('idx_order_side', 'side'),
        Index('idx_order_submitted', 'submitted_at'),
        Index('idx_order_broker_id', 'broker_order_id'),
    )


class Position(Base):
    """Position tracking"""
    __tablename__ = "positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String(20), nullable=False)

    # Position details
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(15, 6), nullable=False)
    current_price = Column(Numeric(15, 6))
    market_value = Column(Numeric(20, 6))

    # P&L calculations
    unrealized_pnl = Column(Numeric(20, 6))
    unrealized_pnl_percent = Column(Numeric(8, 4))
    realized_pnl = Column(Numeric(20, 6))
    total_pnl = Column(Numeric(20, 6))

    # Position metrics
    average_cost = Column(Numeric(15, 6))
    total_cost = Column(Numeric(20, 6))
    commission_paid = Column(Numeric(15, 6))

    # Position attributes
    side = Column(String(10))  # LONG, SHORT
    status = Column(String(20), default=PositionStatus.OPEN)
    leverage = Column(Numeric(8, 4))

    # Timing
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Risk metrics
    max_unrealized_pnl = Column(Numeric(20, 6))
    max_unrealized_loss = Column(Numeric(20, 6))
    position_var = Column(Numeric(15, 6))

    # Strategy context
    strategy_entry_signal = Column(String(100))
    strategy_exit_signal = Column(String(100))
    entry_reason = Column(Text)
    exit_reason = Column(Text)

    # Metadata
    attributes = Column(JSONB)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    orders = relationship("Order", back_populates="position")

    __table_args__ = (
        Index('idx_position_portfolio', 'portfolio_id'),
        Index('idx_position_symbol', 'symbol'),
        Index('idx_position_status', 'status'),
        Index('idx_position_opened', 'opened_at'),
        Index('idx_position_composite', 'portfolio_id', 'symbol', 'status'),
    )


class Trade(Base):
    """Completed trade records"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False)

    # Trade details
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # LONG, SHORT
    quantity = Column(Numeric(20, 8), nullable=False)
    entry_price = Column(Numeric(15, 6), nullable=False)
    exit_price = Column(Numeric(15, 6))

    # Trade timing
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime)
    duration_hours = Column(Float)

    # P&L calculations
    gross_pnl = Column(Numeric(20, 6))
    commission = Column(Numeric(15, 6))
    net_pnl = Column(Numeric(20, 6))
    net_pnl_percent = Column(Numeric(8, 4))
    return_on_capital = Column(Numeric(8, 4))

    # Trade attributes
    trade_type = Column(String(20))  # OPEN, CLOSE, REVERSE
    status = Column(String(20), default=TradeStatus.EXECUTED)
    exit_reason = Column(String(50))

    # Risk metrics
    max_favorable = Column(Numeric(20, 6))
    max_adverse = Column(Numeric(20, 6))
    sharpe_ratio = Column(Numeric(8, 4))

    # Strategy references
    signal_id = Column(String(100))
    order_id = Column(String(100))
    strategy_name = Column(String(100))

    # Execution details
    execution_venue = Column(String(50))
    liquidity_taker = Column(Boolean, default=True)

    # Metadata
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text)
    tags = Column(JSONB)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")

    __table_args__ = (
        Index('idx_trade_portfolio', 'portfolio_id'),
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_executed', 'executed_at'),
        Index('idx_trade_entry_date', 'entry_date'),
        Index('idx_trade_status', 'status'),
    )


class TradingSession(Base):
    """Trading session logs"""
    __tablename__ = "trading_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)

    # Session details
    session_name = Column(String(200))
    session_type = Column(String(20))  # backtest, simulation, live

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Session configuration
    configuration = Column(JSONB)
    market_data_config = Column(JSONB)
    risk_config = Column(JSONB)

    # Session results
    initial_capital = Column(Numeric(15, 2))
    final_capital = Column(Numeric(15, 2))
    total_pnl = Column(Numeric(15, 2))
    total_trades = Column(Integer, default=0)

    # Performance metrics
    win_rate = Column(Numeric(5, 2))
    profit_factor = Column(Numeric(8, 2))
    max_drawdown = Column(Numeric(8, 4))
    sharpe_ratio = Column(Numeric(8, 4))

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    status = Column(String(20), default="running")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    strategy_instance = relationship("StrategyInstance")

    __table_args__ = (
        Index('idx_trading_session_instance', 'strategy_instance_id'),
        Index('idx_trading_session_started', 'started_at'),
        Index('idx_trading_session_status', 'status'),
    )


class TradingSignal(Base):
    """Generated trading signals"""
    __tablename__ = "trading_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_instance_id = Column(UUID(as_uuid=True), ForeignKey("strategy_instances.id"), nullable=False)

    # Signal details
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    signal_type = Column(String(50))  # ENTRY, EXIT, ADJUST

    # Signal parameters
    confidence = Column(Numeric(5, 4))
    strength = Column(Numeric(5, 4))
    entry_price = Column(Numeric(15, 6))
    target_price = Column(Numeric(15, 6))
    stop_loss = Column(Numeric(15, 6))
    position_size = Column(Numeric(20, 8))

    # Signal source
    strategy_name = Column(String(100))
    indicator_name = Column(String(100))
    source = Column(String(100))

    # Context data
    market_data = Column(JSONB)
    indicators = Column(JSONB)
    alternative_data = Column(JSONB)

    # Execution
    status = Column(String(20), default="pending")  # pending, executed, expired, cancelled
    executed_at = Column(DateTime)
    order_id = Column(String(100))

    # Signal timing
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)

    # Metadata
    reason = Column(Text)
    tags = Column(JSONB)

    # Relationships
    strategy_instance = relationship("StrategyInstance")

    __table_args__ = (
        Index('idx_trading_signal_instance', 'strategy_instance_id'),
        Index('idx_trading_signal_symbol', 'symbol'),
        Index('idx_trading_signal_generated', 'generated_at'),
        Index('idx_trading_signal_status', 'status'),
    )