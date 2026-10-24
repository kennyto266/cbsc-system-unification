"""
交易和投資組合模型

定義交易訂單、持倉、投資組合等相關的數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, NUMERIC
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import enum

from .unified_base import UnifiedBaseModel, UnifiedSchema, StatusEnum

class OrderType(str, enum.Enum):
    """訂單類型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(str, enum.Enum):
    """訂單方向"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    """訂單狀態"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PositionSide(str, enum.Enum):
    """持倉方向"""
    LONG = "long"
    SHORT = "short"

class Order(UnifiedBaseModel):
    """交易訂單模型"""

    __tablename__ = 'orders'

    # 基本信息標識
    external_order_id = Column(String(100), nullable=True, index=True)  # 外部系統訂單ID
    strategy_id = Column(String(36), ForeignKey('strategies.id'), nullable=True)
    strategy_config_id = Column(String(36), ForeignKey('strategy_configs.id'), nullable=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    portfolio_id = Column(String(36), ForeignKey('portfolios.id'), nullable=True)

    # 訂單基本屬性
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)

    # 訂單類型和方向
    order_type = Column(Enum(OrderType), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)

    # 數量和價格
    quantity = Column(Integer, nullable=False)
    price = Column(NUMERIC(15, 4), nullable=True)  # 限價訂單的價格
    stop_price = Column(NUMERIC(15, 4), nullable=True)  # 止損價格
    filled_quantity = Column(Integer, default=0, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)

    # 執行信息
    time_in_force = Column(String(20), default="GTC", nullable=False)  # GTC, IOC, FOK, DAY
    execution_time = Column(DateTime(timezone=True), nullable=True)
    average_fill_price = Column(NUMERIC(15, 4), nullable=True)

    # 成本和費用
    commission = Column(NUMERIC(15, 4), default=0, nullable=False)
    slippage = Column(NUMERIC(15, 4), default=0, nullable=False)
    taxes = Column(NUMERIC(15, 4), default=0, nullable=False)
    total_cost = Column(NUMERIC(15, 4), nullable=False)

    # 風險控制
    stop_loss_price = Column(NUMERIC(15, 4), nullable=True)
    take_profit_price = Column(NUMERIC(15, 4), nullable=True)
    trailing_stop_percent = Column(Float, nullable=True)

    # 訂單原因和標籤
    order_reason = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    # 外部系統信息
    broker = Column(String(50), nullable=True)
    submitted_to_broker = Column(Boolean, default=False, nullable=False)
    broker_response = Column(JSONB, nullable=True)

    # 關聯
    strategy = relationship("Strategy")
    strategy_config = relationship("StrategyConfig")
    user = relationship("User")
    portfolio = relationship("Portfolio")
    trades = relationship("Trade", back_populates="order")

    def calculate_total_cost(self):
        """計算訂單總成本"""
        if self.filled_quantity > 0 and self.average_fill_price:
            base_cost = self.filled_quantity * self.average_fill_price
            self.total_cost = base_cost + self.commission + self.taxes

    def update_status(self, new_status: OrderStatus, filled_qty: Optional[int] = None, fill_price: Optional[Decimal] = None):
        """更新訂單狀態"""
        old_status = self.status
        self.status = new_status

        if filled_qty is not None:
            self.filled_quantity += filled_qty
            self.remaining_quantity = self.quantity - self.filled_quantity

            if fill_price is not None:
                # 計算平均成交價
                if self.average_fill_price is None:
                    self.average_fill_price = fill_price
                else:
                    total_value = (self.filled_quantity - filled_qty) * self.average_fill_price + filled_qty * fill_price
                    self.average_fill_price = total_value / self.filled_quantity

        # 更新執行時間
        if new_status in [OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED] and old_status not in [OrderStatus.FILLED, OrderStatus.PARTIAL_FILLED]:
            self.execution_time = datetime.now(timezone.utc)

        self.calculate_total_cost()

class Trade(UnifiedBaseModel):
    """交易記錄模型"""

    __tablename__ = 'trades'

    # 關聯信息
    order_id = Column(String(36), ForeignKey('orders.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)
    portfolio_id = Column(String(36), ForeignKey('portfolios.id'), nullable=True)

    # 交易基本信息
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide), nullable=False, index=True)

    # 交易數量和價格
    quantity = Column(Integer, nullable=False)
    price = Column(NUMERIC(15, 4), nullable=False)
    notional = Column(NUMERIC(15, 4), nullable=False)

    # 執行時間和ID
    trade_time = Column(DateTime(timezone=True), nullable=False, index=True)
    external_trade_id = Column(String(100), nullable=True, index=True)
    execution_venue = Column(String(50), nullable=True)

    # 成本和費用
    commission = Column(NUMERIC(15, 4), default=0, nullable=False)
    slippage = Column(NUMERIC(15, 4), default=0, nullable=False)
    taxes = Column(NUMERIC(15, 4), default=0, nullable=False)
    total_cost = Column(NUMERIC(15, 4), nullable=False)

    # 清算信息
    settlement_date = Column(DateTime(timezone=True), nullable=True)
    settlement_currency = Column(String(10), nullable=True)
    fx_rate = Column(NUMERIC(12, 6), default=1.0, nullable=False)

    # 交易原因和分析
    trade_reason = Column(String(100), nullable=True)
    strategy_signal = Column(JSONB, nullable=True)
    market_conditions = Column(JSONB, nullable=True)

    # 審計信息
    broker_reference = Column(String(100), nullable=True)
    clearing_firm = Column(String(100), nullable=True)

    # 關聯
    order = relationship("Order", back_populates="trades")
    user = relationship("User")
    portfolio = relationship("Portfolio")

    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        """計算盈虧"""
        if self.side == OrderSide.BUY:
            return (current_price - self.price) * self.quantity - self.total_cost
        else:  # SELL
            return (self.price - current_price) * self.quantity - self.total_cost

class Position(UnifiedBaseModel):
    """持倉模型"""

    __tablename__ = 'positions'

    # 關聯信息
    portfolio_id = Column(String(36), ForeignKey('portfolios.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)

    # 持倉基本信息
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    asset_type = Column(String(20), nullable=False)
    side = Column(Enum(PositionSide), nullable=False, index=True)

    # 持倉數量
    quantity = Column(Integer, nullable=False, default=0)
    available_quantity = Column(Integer, nullable=False, default=0)  # 可用數量（未鎖定）

    # 成本信息
    average_cost = Column(NUMERIC(15, 4), nullable=False)
    total_cost = Column(NUMERIC(15, 4), nullable=False)
    commission_paid = Column(NUMERIC(15, 4), default=0, nullable=False)

    # 當前價值和盈虧
    current_price = Column(NUMERIC(15, 4), nullable=True)
    market_value = Column(NUMERIC(15, 4), nullable=False)
    unrealized_pnl = Column(NUMERIC(15, 4), default=0, nullable=False)
    unrealized_pnl_percent = Column(Float, default=0.0, nullable=False)

    # 已實現盈虧
    realized_pnl = Column(NUMERIC(15, 4), default=0, nullable=False)
    total_pnl = Column(NUMERIC(15, 4), default=0, nullable=False)

    # 持倉時間
    first_opened = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=False)

    # 風險指標
    max_price = Column(NUMERIC(15, 4), nullable=True)
    min_price = Column(NUMERIC(15, 4), nullable=True)
    max_unrealized_pnl = Column(NUMERIC(15, 4), nullable=True)
    max_drawdown = Column(NUMERIC(15, 4), nullable=True)

    # 持倉標籤和元數據
    tags = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)

    # 關聯
    portfolio = relationship("Portfolio", back_populates="positions")
    user = relationship("User")

    def update_market_data(self, new_price: Decimal):
        """更新市場數據"""
        old_price = self.current_price or Decimal('0')
        self.current_price = new_price
        self.last_updated = datetime.now(timezone.utc)

        # 計算市值
        self.market_value = abs(self.quantity) * new_price

        # 計算未實現盈虧
        if self.quantity != 0:
            if self.side == PositionSide.LONG:
                self.unrealized_pnl = (new_price - self.average_cost) * self.quantity
            else:  # SHORT
                self.unrealized_pnl = (self.average_cost - new_price) * abs(self.quantity)

            if self.total_cost != 0:
                self.unrealized_pnl_percent = float(self.unrealized_pnl / abs(self.total_cost) * 100)

        # 更新最高/最低價格和最大未實現盈虧
        if self.max_price is None or new_price > self.max_price:
            self.max_price = new_price
        if self.min_price is None or new_price < self.min_price:
            self.min_price = new_price

        if self.unrealized_pnl > (self.max_unrealized_pnl or Decimal('0')):
            self.max_unrealized_pnl = self.unrealized_pnl

        # 計算總盈虧
        self.total_pnl = self.realized_pnl + self.unrealized_pnl

class Portfolio(UnifiedBaseModel):
    """投資組合模型"""

    __tablename__ = 'portfolios'

    # 基本信息標識
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(String(50), default="discretionary", nullable=False)  # discretionary, systematic, advisory

    # 現金和資金
    cash_balance = Column(NUMERIC(20, 4), nullable=False)
    available_cash = Column(NUMERIC(20, 4), nullable=False)
    total_value = Column(NUMERIC(20, 4), nullable=False)
    allocated_capital = Column(NUMERIC(20, 4), nullable=False)
    unallocated_capital = Column(NUMERIC(20, 4), nullable=False)

    # 性能指標
    total_return = Column(NUMERIC(10, 4), default=0, nullable=False)
    total_return_percent = Column(Float, default=0.0, nullable=False)
    daily_return = Column(NUMERIC(10, 4), default=0, nullable=False)
    daily_return_percent = Column(Float, default=0.0, nullable=False)

    # 風險指標
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, default=0.0, nullable=False)
    var_95 = Column(Float, nullable=True)

    # 統計信息
    total_positions = Column(Integer, default=0, nullable=False)
    active_positions = Column(Integer, default=0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)

    # 基準比較
    benchmark_symbol = Column(String(20), nullable=True)
    benchmark_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)

    # 配置和限制
    max_positions = Column(Integer, nullable=True)
    max_position_size = Column(Float, nullable=True)  # 百分比
    risk_limit = Column(Float, nullable=True)

    # 狀態和時間
    is_active = Column(Boolean, default=True, nullable=False)
    inception_date = Column(DateTime(timezone=True), nullable=False)
    last_rebalanced = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")

    def calculate_total_value(self):
        """計算投資組合總價值"""
        positions_value = sum(pos.market_value for pos in self.positions if pos.quantity != 0)
        self.total_value = self.cash_balance + positions_value
        self.available_cash = self.cash_balance  # 可以根據掛單等調整
        self.unallocated_capital = self.available_cash

        # 更新統計
        self.total_positions = len(self.positions)
        self.active_positions = len([pos for pos in self.positions if pos.quantity != 0])

    def calculate_daily_return(self, previous_total: Decimal):
        """計算日收益率"""
        if previous_total and previous_total != 0:
            daily_change = self.total_value - previous_total
            self.daily_return = daily_change
            self.daily_return_percent = float(daily_change / abs(previous_total) * 100)

# Pydantic Schemas
class OrderBaseSchema(UnifiedSchema):
    """訂單基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    exchange: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field(..., description="資產類型")
    order_type: OrderType
    side: OrderSide
    quantity: int = Field(..., gt=0, description="訂單數量")
    price: Optional[Decimal] = Field(None, gt=0, description="限價")
    stop_price: Optional[Decimal] = Field(None, gt=0, description="止損價")
    time_in_force: str = Field("GTC", description="時效性")

class OrderCreateSchema(OrderBaseSchema):
    """創建訂單Schema"""
    strategy_id: Optional[str] = None
    strategy_config_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    order_reason: Optional[str] = None
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None

class OrderResponseSchema(OrderBaseSchema):
    """訂單響應Schema"""
    external_order_id: Optional[str] = None
    status: OrderStatus
    filled_quantity: int
    remaining_quantity: int
    average_fill_price: Optional[Decimal] = None
    commission: Decimal
    total_cost: Decimal
    execution_time: Optional[datetime] = None
    strategy_name: Optional[str] = None
    portfolio_name: Optional[str] = None

    class Config:
        from_attributes = True

class TradeBaseSchema(UnifiedSchema):
    """交易記錄基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    exchange: str
    asset_type: str
    side: OrderSide
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    trade_time: datetime

class TradeResponseSchema(TradeBaseSchema):
    """交易記錄響應Schema"""
    order_id: str
    notional: Decimal
    commission: Decimal
    total_cost: Decimal
    external_trade_id: Optional[str] = None
    execution_venue: Optional[str] = None
    settlement_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class PositionBaseSchema(UnifiedSchema):
    """持倉基礎Schema"""
    symbol: str = Field(..., min_length=1, max_length=20)
    exchange: str
    asset_type: str
    side: PositionSide
    quantity: int
    average_cost: Decimal

class PositionResponseSchema(PositionBaseSchema):
    """持倉響應Schema"""
    available_quantity: int
    total_cost: Decimal
    current_price: Optional[Decimal] = None
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float
    realized_pnl: Decimal
    total_pnl: Decimal
    first_opened: Optional[datetime] = None
    last_updated: datetime
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True

class PortfolioBaseSchema(UnifiedSchema):
    """投資組合基礎Schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    portfolio_type: str = Field("discretionary", description="投資組合類型")
    allocated_capital: Decimal = Field(..., ge=0, description="分配資本")
    max_positions: Optional[int] = Field(None, gt=0, description="最大持倉數")
    max_position_size: Optional[float] = Field(None, gt=0, le=1, description="最大單個持倉比例")
    risk_limit: Optional[float] = Field(None, gt=0, description="風險限制")

class PortfolioCreateSchema(PortfolioBaseSchema):
    """創建投資組合Schema"""
    benchmark_symbol: Optional[str] = None

class PortfolioResponseSchema(PortfolioBaseSchema):
    """投資組合響應Schema"""
    cash_balance: Decimal
    available_cash: Decimal
    total_value: Decimal
    unallocated_capital: Decimal
    total_return: Decimal
    total_return_percent: float
    daily_return: Decimal
    daily_return_percent: float
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: float
    total_positions: int
    active_positions: int
    benchmark_symbol: Optional[str] = None
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    is_active: bool
    inception_date: datetime
    last_rebalanced: Optional[datetime] = None

    class Config:
        from_attributes = True