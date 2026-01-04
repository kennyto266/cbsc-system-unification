"""
Unified CBSC System Models - SQLAlchemy 2.0
This module contains all database models for the CBSC Trading System.
Compatible with SQLAlchemy 2.0+ using modern Mapped[] syntax.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, JSON, ForeignKey,
    DateTime, DECIMAL, BIGINT, Index, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models with async support"""
    pass


# ============================================================================
# Mixins
# ============================================================================

class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        onupdate='NOW()',
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )


# ============================================================================
# User & Authentication Models
# ============================================================================

class User(Base, TimestampMixin):
    """User account information"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        default=None
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationships
    roles: Mapped[List['UserRole']] = relationship(
        'UserRole',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    strategies: Mapped[List['Strategy']] = relationship(
        'Strategy',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    api_keys: Mapped[List['ApiKey']] = relationship(
        'ApiKey',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    webhooks: Mapped[List['Webhook']] = relationship(
        'Webhook',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    preferences: Mapped[List['UserPreference']] = relationship(
        'UserPreference',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    activities: Mapped[List['UserActivity']] = relationship(
        'UserActivity',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    mfa_devices: Mapped[List['MfaDevice']] = relationship(
        'MfaDevice',
        back_populates='user',
        cascade='all, delete-orphan'
    )
    portfolios: Mapped[List['Portfolio']] = relationship(
        'Portfolio',
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<User(id={self.id}, username="{self.username}")>'


class Role(Base, TimestampMixin):
    """User roles for RBAC"""
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    permissions: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationships
    users: Mapped[List['UserRole']] = relationship(
        'UserRole',
        back_populates='role',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Role(id={self.id}, name="{self.name}")>'


class UserRole(Base):
    """Association table for User-Role many-to-many relationship"""
    __tablename__ = 'user_roles'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='roles')
    role: Mapped['Role'] = relationship('Role', back_populates='users')

    __table_args__ = (
        Index('idx_user_roles_user_id', 'user_id'),
        Index('idx_user_roles_role_id', 'role_id'),
    )


class MfaDevice(Base, TimestampMixin):
    """Multi-factor authentication devices"""
    __tablename__ = 'mfa_devices'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='mfa_devices')

    def __repr__(self) -> str:
        return f'<MfaDevice(id={self.id}, user_id={self.user_id}, type="{self.device_type}")>'


# ============================================================================
# Strategy Management Models
# ============================================================================

class Strategy(Base, TimestampMixin):
    """Trading strategies"""
    __tablename__ = 'strategies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    category: Mapped[str] = mapped_column(
        String(50),
        default='custom',
        nullable=False,
        index=True
    )
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default='draft',
        nullable=False,
        index=True
    )
    last_run: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )
    performance: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        default=None
    )

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='strategies')
    strategy_configs: Mapped[List['StrategyConfig']] = relationship(
        'StrategyConfig',
        back_populates='strategy',
        cascade='all, delete-orphan'
    )
    strategy_performance: Mapped[List['StrategyPerformance']] = relationship(
        'StrategyPerformance',
        back_populates='strategy',
        cascade='all, delete-orphan'
    )
    trades: Mapped[List['Trade']] = relationship(
        'Trade',
        back_populates='strategy',
        cascade='all, delete-orphan'
    )
    backtest_results: Mapped[List['BacktestResult']] = relationship(
        'BacktestResult',
        back_populates='strategy',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Strategy(id={self.id}, name="{self.name}", status="{self.status}")>'


class StrategyConfig(Base, TimestampMixin):
    """Strategy configuration parameters"""
    __tablename__ = 'strategy_configs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey('strategies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameter_value: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )

    # Relationships
    strategy: Mapped['Strategy'] = relationship('Strategy', back_populates='strategy_configs')

    def __repr__(self) -> str:
        return f'<StrategyConfig(id={self.id}, strategy_id={self.strategy_id}, param="{self.parameter_name}")>'


class StrategyPerformance(Base):
    """Historical strategy performance metrics"""
    __tablename__ = 'strategy_performance'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey('strategies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    total_return: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    max_drawdown: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    win_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4), default=None)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    strategy: Mapped['Strategy'] = relationship('Strategy', back_populates='strategy_performance')

    def __repr__(self) -> str:
        return f'<StrategyPerformance(id={self.id}, strategy_id={self.strategy_id})>'


# ============================================================================
# Trading & Portfolio Models
# ============================================================================

class Portfolio(Base, TimestampMixin):
    """User portfolios for tracking holdings"""
    __tablename__ = 'portfolios'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_value: Mapped[float] = mapped_column(
        DECIMAL(18, 8),
        default=0,
        nullable=False
    )
    cash_balance: Mapped[float] = mapped_column(
        DECIMAL(18, 8),
        default=0,
        nullable=False
    )
    holdings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='portfolios')
    trades: Mapped[List['Trade']] = relationship(
        'Trade',
        back_populates='portfolio',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<Portfolio(id={self.id}, name="{self.name}", value={self.total_value})>'


class Trade(Base, TimestampMixin):
    """Trade execution records"""
    __tablename__ = 'trades'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('strategies.id', ondelete='SET NULL'),
        index=True
    )
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey('portfolios.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # 'buy' or 'sell'
    quantity: Mapped[float] = mapped_column(DECIMAL(18, 8), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(18, 8), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default='pending',
        nullable=False
    )

    # Relationships
    strategy: Mapped[Optional['Strategy']] = relationship('Strategy', back_populates='trades')
    portfolio: Mapped['Portfolio'] = relationship('Portfolio', back_populates='trades')

    def __repr__(self) -> str:
        return f'<Trade(id={self.id}, symbol="{self.symbol}", side="{self.side}")>'


# ============================================================================
# Market Data Models
# ============================================================================

class MarketData(Base):
    """Historical and real-time market data"""
    __tablename__ = 'market_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    open_price: Mapped[Optional[float]] = mapped_column(DECIMAL(18, 8), default=None)
    high_price: Mapped[Optional[float]] = mapped_column(DECIMAL(18, 8), default=None)
    low_price: Mapped[Optional[float]] = mapped_column(DECIMAL(18, 8), default=None)
    close_price: Mapped[Optional[float]] = mapped_column(DECIMAL(18, 8), default=None)
    volume: Mapped[Optional[int]] = mapped_column(BIGINT, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    technical_indicators: Mapped[List['TechnicalIndicator']] = relationship(
        'TechnicalIndicator',
        back_populates='market_data',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f'<MarketData(id={self.id}, symbol="{self.symbol}", timestamp={self.timestamp})>'


class TechnicalIndicator(Base):
    """Calculated technical indicators"""
    __tablename__ = 'technical_indicators'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_data_id: Mapped[int] = mapped_column(
        ForeignKey('market_data.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    indicator_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    indicator_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    market_data: Mapped['MarketData'] = relationship('MarketData', back_populates='technical_indicators')

    def __repr__(self) -> str:
        return f'<TechnicalIndicator(id={self.id}, name="{self.indicator_name}")>'


class SentimentData(Base):
    """Market sentiment data from various sources"""
    __tablename__ = 'sentiment_data'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 4), default=None)
    source: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    def __repr__(self) -> str:
        return f'<SentimentData(id={self.id}, symbol="{self.symbol}", score={self.sentiment_score})>'


# ============================================================================
# Analytics & Backtesting Models
# ============================================================================

class BacktestResult(Base):
    """Backtest execution results"""
    __tablename__ = 'backtest_results'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey('strategies.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    initial_capital: Mapped[float] = mapped_column(DECIMAL(18, 8), nullable=False)
    final_value: Mapped[float] = mapped_column(DECIMAL(18, 8), nullable=False)
    total_return: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    max_drawdown: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 4), default=None)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detailed_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    strategy: Mapped['Strategy'] = relationship('Strategy', back_populates='backtest_results')
    analysis_reports: Mapped[List['AnalysisReport']] = relationship(
        'AnalysisReport',
        back_populates='backtest',
        cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<BacktestResult(id={self.id}, strategy_id={self.strategy_id}, return={self.total_return})>'


class AnalysisReport(Base):
    """Generated analysis reports for backtests"""
    __tablename__ = 'analysis_reports'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[int] = mapped_column(
        ForeignKey('backtest_results.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False
    )

    # Relationships
    backtest: Mapped['BacktestResult'] = relationship('BacktestResult', back_populates='analysis_reports')

    def __repr__(self) -> str:
        return f'<AnalysisReport(id={self.id}, type="{self.report_type}", status="{self.status}")>'


# ============================================================================
# API & Security Models
# ============================================================================

class ApiKey(Base, TimestampMixin):
    """User API keys for programmatic access"""
    __tablename__ = 'api_keys'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='api_keys')

    def __repr__(self) -> str:
        return f'<ApiKey(id={self.id}, name="{self.name}", active={self.is_active})>'


class Webhook(Base, TimestampMixin):
    """User webhook configurations"""
    __tablename__ = 'webhooks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    events: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='webhooks')

    def __repr__(self) -> str:
        return f'<Webhook(id={self.id}, url="{self.url}", active={self.is_active})>'


# ============================================================================
# User Preferences & Activity Models
# ============================================================================

class UserPreference(Base, TimestampMixin):
    """User-specific preferences and settings"""
    __tablename__ = 'user_preferences'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    preference_key: Mapped[str] = mapped_column(String(100), nullable=False)
    preference_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='preferences')

    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uq_user_preference'),
        Index('idx_user_preferences_user_id', 'user_id'),
    )

    def __repr__(self) -> str:
        return f'<UserPreference(id={self.id}, user_id={self.user_id}, key="{self.preference_key}")>'


class UserActivity(Base):
    """User activity logging for audit trail"""
    __tablename__ = 'user_activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=None)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), default=None)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default='NOW()',
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='activities')

    def __repr__(self) -> str:
        return f'<UserActivity(id={self.id}, user_id={self.user_id}, action="{self.action}")>'


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Base
    'Base',

    # Mixins
    'TimestampMixin',
    'SoftDeleteMixin',

    # User & Authentication
    'User',
    'Role',
    'UserRole',
    'MfaDevice',

    # Strategy Management
    'Strategy',
    'StrategyConfig',
    'StrategyPerformance',

    # Trading & Portfolio
    'Portfolio',
    'Trade',

    # Market Data
    'MarketData',
    'TechnicalIndicator',
    'SentimentData',

    # Analytics & Backtesting
    'BacktestResult',
    'AnalysisReport',

    # API & Security
    'ApiKey',
    'Webhook',

    # User Preferences & Activity
    'UserPreference',
    'UserActivity',
]
