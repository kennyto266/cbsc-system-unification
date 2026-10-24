"""
策略管理模型

定義策略、策略配置、策略性能等相關的數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from .unified_base import UnifiedBaseModel, UnifiedSchema, StatusEnum, RiskLevelEnum

class StrategyCategory(UnifiedBaseModel):
    """策略分類模型"""

    __tablename__ = 'strategy_categories'

    # 基本信息
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # 分類層級
    parent_id = Column(String(36), ForeignKey('strategy_categories.id'), nullable=True)
    level = Column(Integer, default=0, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 關聯
    parent = relationship("StrategyCategory", remote_side="StrategyCategory.id")
    children = relationship("StrategyCategory", back_populates="parent")
    strategies = relationship("Strategy", back_populates="category")

class Strategy(UnifiedBaseModel):
    """策略模型"""

    __tablename__ = 'strategies'

    # 基本信息
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 分類
    category_id = Column(String(36), ForeignKey('strategy_categories.id'), nullable=True)
    strategy_type = Column(String(50), nullable=False, index=True)  # technical, fundamental, sentiment, etc.

    # 狀態和風險
    status = Column(String(20), default=StatusEnum.INACTIVE, nullable=False, index=True)
    risk_level = Column(String(20), default=RiskLevelEnum.MEDIUM, nullable=False, index=True)

    # 性能指標
    total_return = Column(Float, default=0.0, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0.0, nullable=False)
    win_rate = Column(Float, default=0.0, nullable=False)
    profit_factor = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)

    # 配置和參數
    default_parameters = Column(JSONB, nullable=True)
    required_indicators = Column(JSONB, nullable=True)
    supported_timeframes = Column(JSONB, nullable=True)

    # 版本控制
    version = Column(String(20), default="1.0.0", nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # 統計信息
    total_users = Column(Integer, default=0, nullable=False)
    active_users = Column(Integer, default=0, nullable=False)
    total_signals = Column(Integer, default=0, nullable=False)

    # 關聯
    category = relationship("StrategyCategory", back_populates="strategies")
    configs = relationship("StrategyConfig", back_populates="strategy")
    performance_records = relationship("StrategyPerformance", back_populates="strategy")

class StrategyConfig(UnifiedBaseModel):
    """策略配置模型"""

    __tablename__ = 'strategy_configs'

    # 關聯
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)

    # 配置信息
    config_name = Column(String(200), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # 個人化參數
    custom_parameters = Column(JSONB, nullable=True)
    risk_tolerance = Column(String(20), default="moderate", nullable=False)
    capital_allocation = Column(Float, default=0.0, nullable=False)
    max_position_size = Column(Float, default=1.0, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    # 自動交易設置
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    auto_rebalance = Column(Boolean, default=False, nullable=False)
    rebalance_frequency = Column(String(20), default="daily", nullable=False)

    # 通知設置
    notifications = Column(JSONB, nullable=True)

    # 狀態
    is_active = Column(Boolean, default=True, nullable=False)

    # 關聯
    strategy = relationship("Strategy", back_populates="configs")
    user = relationship("User", back_populates="strategy_configs")

class StrategyPerformance(UnifiedBaseModel):
    """策略性能模型"""

    __tablename__ = 'strategy_performance'

    # 關聯
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=False)
    config_id = Column(String(36), ForeignKey('strategy_configs.id'), nullable=True)

    # 性能數據
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_return = Column(Float, nullable=False)
    daily_return = Column(Float, nullable=True)
    cumulative_return = Column(Float, nullable=False)
    benchmark_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)

    # 風險指標
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)
    cvar_95 = Column(Float, nullable=True)

    # 交易統計
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Float, default=0.0, nullable=False)
    profit_factor = Column(Float, nullable=True)
    average_win = Column(Float, nullable=True)
    average_loss = Column(Float, nullable=True)

    # 持倉信息
    current_positions = Column(Integer, default=0, nullable=False)
    open_positions_value = Column(Float, default=0.0, nullable=False)
    cash_balance = Column(Float, default=0.0, nullable=False)

    # 元數據
    market_conditions = Column(JSONB, nullable=True)
    data_quality_score = Column(Float, default=1.0, nullable=False)

    # 關聯
    strategy = relationship("Strategy", back_populates="performance_records")
    config = relationship("StrategyConfig")

# Pydantic Schemas
class StrategyCategoryBaseSchema(UnifiedSchema):
    """策略分類基礎Schema"""
    name: str = Field(..., min_length=3, max_length=100, description="分類名稱")
    display_name: str = Field(..., min_length=3, max_length=200, description="顯示名稱")
    description: Optional[str] = Field(None, description="分類描述")
    parent_id: Optional[str] = Field(None, description="父分類ID")
    level: int = Field(0, ge=0, description="分類層級")
    sort_order: int = Field(0, ge=0, description="排序順序")

class StrategyCategoryResponseSchema(StrategyCategoryBaseSchema):
    """策略分類響應Schema"""
    is_active: bool
    children_count: int = 0
    strategies_count: int = 0

    class Config:
        from_attributes = True

class StrategyBaseSchema(UnifiedSchema):
    """策略基礎Schema"""
    name: str = Field(..., min_length=3, max_length=200, description="策略名稱")
    code: str = Field(..., min_length=3, max_length=100, description="策略代碼")
    description: Optional[str] = Field(None, description="策略描述")
    category_id: Optional[str] = Field(None, description="分類ID")
    strategy_type: str = Field(..., description="策略類型")
    risk_level: str = Field(RiskLevelEnum.MEDIUM, description="風險等級")
    default_parameters: Optional[Dict[str, Any]] = Field(None, description="默認參數")
    required_indicators: Optional[List[str]] = Field(None, description="必需指標")
    supported_timeframes: Optional[List[str]] = Field(None, description="支持的時間週期")

class StrategyCreateSchema(StrategyBaseSchema):
    """創建策略Schema"""
    pass

class StrategyUpdateSchema(UnifiedSchema):
    """更新策略Schema"""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    default_parameters: Optional[Dict[str, Any]] = None

class StrategyResponseSchema(StrategyBaseSchema):
    """策略響應Schema"""
    status: str
    total_return: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    win_rate: float
    profit_factor: Optional[float]
    version: str
    is_public: bool
    total_users: int
    active_users: int
    total_signals: int
    category: Optional[str] = None

    class Config:
        from_attributes = True

class StrategyConfigBaseSchema(UnifiedSchema):
    """策略配置基礎Schema"""
    config_name: str = Field(..., min_length=3, max_length=200, description="配置名稱")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="自定義參數")
    risk_tolerance: str = Field("moderate", description="風險容忍度")
    capital_allocation: float = Field(0.0, ge=0, description="資金分配")
    max_position_size: float = Field(1.0, gt=0, le=1, description="最大持倉比例")
    stop_loss: Optional[float] = Field(None, gt=0, description="止損比例")
    take_profit: Optional[float] = Field(None, gt=0, description="止盈比例")

class StrategyConfigCreateSchema(StrategyConfigBaseSchema):
    """創建策略配置Schema"""
    strategy_id: str = Field(..., description="策略ID")
    notifications: Optional[Dict[str, Any]] = Field(None, description="通知設置")

class StrategyConfigResponseSchema(StrategyConfigBaseSchema):
    """策略配置響應Schema"""
    strategy_id: str
    strategy_name: Optional[str] = None
    user_id: Optional[str] = None
    is_default: bool
    auto_trading_enabled: bool
    auto_rebalance: bool
    rebalance_frequency: str
    is_active: bool

    class Config:
        from_attributes = True

class StrategyPerformanceBaseSchema(UnifiedSchema):
    """策略性能基礎Schema"""
    strategy_id: str
    date: datetime
    total_return: float
    daily_return: Optional[float]
    cumulative_return: float
    benchmark_return: Optional[float]
    alpha: Optional[float]
    volatility: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: float = 0.0
    total_trades: int = 0

class StrategyPerformanceResponseSchema(StrategyPerformanceBaseSchema):
    """策略性能響應Schema"""
    strategy_name: Optional[str] = None
    sortino_ratio: Optional[float]
    var_95: Optional[float]
    cvar_95: Optional[float]
    profit_factor: Optional[float]
    average_win: Optional[float]
    average_loss: Optional[float]
    current_positions: int
    open_positions_value: float
    cash_balance: float
    data_quality_score: float

    class Config:
        from_attributes = True