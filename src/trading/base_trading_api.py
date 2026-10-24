"""
交易API基礎類 - 定義統一的交易接口

支持多種券商和交易所的統一交易接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class OrderTypestr, Enum:
"""訂單類型"""
MARKET = "market" # 市價單
LIMIT = "limit" # 限價單
STOP = "stop" # 止損單
STOP_LIMIT = "stop_limit" # 止損限價單
TRAILING_STOP = "trailing_stop" # 追蹤止損單

class OrderSidestr, Enum:
"""訂單方向"""
BUY = "buy"
SELL = "sell"
SHORT = "short" # 做空
COVER = "cover" # 平倉

class OrderStatusstr, Enum:
"""訂單狀態"""
PENDING = "pending" # 待處理
SUBMITTED = "submitted" # 已提交
FILLED = "filled" # 已成交
PARTIALLY_FILLED = "partially_filled" # 部分成交
CANCELLED = "cancelled" # 已取消
REJECTED = "rejected" # 已拒絕
EXPIRED = "expired" # 已過期

class OrderBaseModel:
"""訂單模型"""
order_id: str = Field..., description="訂單ID"
symbol: str = Field..., description="交易標的"
side: OrderSide = Field..., description="訂單方向"
order_type: OrderType = Field..., description="訂單類型"
quantity: Decimal = Field..., gt=0, description="數量"
price: Optional[Decimal] = FieldNone, description="價格（限價單）"
stop_price: Optional[Decimal] = FieldNone, description="止損價格"
status: OrderStatus = Fielddefault=OrderStatus.PENDING, description="訂單狀態"
filled_quantity: Decimal = Field(default=Decimal'0', description="已成交數量")
average_fill_price: Optional[Decimal] = FieldNone, description="平均成交價格"
commission: Optional[Decimal] = FieldNone, description="手續費"
created_at: datetime = Fielddefault_factory=datetime.now, description="創建時間"
updated_at: datetime = Fielddefault_factory=datetime.now, description="更新時間"
expires_at: Optional[datetime] = FieldNone, description="過期時間"
client_order_id: Optional[str] = FieldNone, description="客戶訂單ID"
notes: Optional[str] = FieldNone, description="備註"

class Config:    use_enum_values = True

class PositionBaseModel:
"""持倉模型"""
symbol: str = Field..., description="交易標的"
quantity: Decimal = Field..., description="持倉數量"
average_price: Decimal = Field..., description="平均成本"
current_price: Optional[Decimal] = FieldNone, description="當前價格"
market_value: Optional[Decimal] = FieldNone, description="市值"
unrealized_pnl: Optional[Decimal] = FieldNone, description="未實現損益"
realized_pnl: Optional[Decimal] = FieldNone, description="已實現損益"
last_updated: datetime = Fielddefault_factory=datetime.now, description="最後更新時間"

@property
def total_valueself -> Optional[Decimal]:
"""總價值"""
if self.market_value is not None:
return self.market_value
elif self.current_price is not None:
return self.current_price * self.quantity
return None

class AccountInfoBaseModel:
"""賬戶信息"""
account_id: str = Field..., description="賬戶ID"
account_type: str = Field..., description="賬戶類型"
buying_power: Optional[Decimal] = FieldNone, description="購買力"
cash: Optional[Decimal] = FieldNone, description="現金餘額"
equity: Optional[Decimal] = FieldNone, description="權益"
margin_used: Optional[Decimal] = FieldNone, description="已用保證金"
margin_available: Optional[Decimal] = FieldNone, description="可用保證金"
day_trading_buying_power: Optional[Decimal] = FieldNone, description="日內交易購買力"
last_updated: datetime = Fielddefault_factory=datetime.now, description="最後更新時間"

class MarketDataBaseModel:
"""市場數據"""
symbol: str = Field..., description="交易標的"
bid_price: Optional[Decimal] = FieldNone, description="買入價"
ask_price: Optional[Decimal] = FieldNone, description="賣出價"
last_price: Optional[Decimal] = FieldNone, description="最新價"
volume: Optional[int] = FieldNone, description="成交量"
high_price: Optional[Decimal] = FieldNone, description="最高價"
low_price: Optional[Decimal] = FieldNone, description="最低價"
open_price: Optional[Decimal] = FieldNone, description="開盤價"
timestamp: datetime = Fielddefault_factory=datetime.now, description="時間戳"

class BaseTradingAPIABC:
"""交易API基礎類"""

def __init__self, config: Dict[str, Any]:    self.config = config
self.logger = logging.getLoggerf"hk_quant_system.trading.{self.__class__.__name__}"
self._connected = False
self._authenticated = False

@abstractmethod
async def connectself -> bool:
"""連接到交易API"""
pass

@abstractmethod
async def disconnectself -> bool:
"""斷開連接"""
pass

@abstractmethod
async def authenticateself, credentials: Dict[str, str] -> bool:
"""身份驗證"""
pass

@abstractmethod
async def get_account_infoself -> Optional[AccountInfo]:
"""獲取賬戶信息"""
pass

@abstractmethod
async def get_positionsself -> List[Position]:
"""獲取持倉信息"""
pass

@abstractmethod
async def get_ordersself, status_filter: Optional[OrderStatus] = None -> List[Order]:
"""獲取訂單列表"""
pass

@abstractmethod
async def place_orderself, order: Order -> Optional[str]:
"""下單"""
pass

@abstractmethod
async def cancel_orderself, order_id: str -> bool:
"""取消訂單"""
pass

@abstractmethod
async def modify_orderself, order_id: str, modifications: Dict[str, Any] -> bool:
"""修改訂單"""
pass

@abstractmethod
async def get_order_statusself, order_id: str -> Optional[OrderStatus]:
"""獲取訂單狀態"""
pass

@abstractmethod
async def get_market_dataself, symbol: str -> Optional[MarketData]:
"""獲取市場數據"""
pass

@abstractmethod
async def get_historical_data(
self, 
symbol: str, 
start_date: datetime, 
end_date: datetime,
interval: str = "1d"
) -> List[Dict[str, Any]]:
"""獲取歷史數據"""
pass

async def health_checkself -> Dict[str, Any]:
"""健康檢查"""
try:
return {
"status": "healthy" if self._connected and self._authenticated else "unhealthy",
"connected": self._connected,
"authenticated": self._authenticated,
"api_type": self.__class__.__name__,
"last_check": datetime.now()
}
except Exception as e:
return {
"status": "error",
"error": stre,
"api_type": self.__class__.__name__,
"last_check": datetime.now()
}

def is_connectedself -> bool:
"""檢查是否已連接"""
return self._connected and self._authenticated

async def validate_orderself, order: Order -> List[str]:
"""驗證訂單"""
errors = []

if not order.symbol:
errors.append"Symbol is required"

if order.quantity <= 0:
errors.append"Quantity must be positive"

if order.order_type == OrderType.LIMIT and not order.price:
errors.append"Price is required for limit orders"

if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and not order.stop_price:
errors.append"Stop price is required for stop orders"

return errors

async def calculate_commissionself, order: Order -> Decimal:
"""計算手續費（默認實現）"""
# 默認手續費計算邏輯
# 實際實現應該根據具體券商的手續費結構
if order.order_type == OrderType.MARKET:
return Decimal'0.01' * order.quantity # 每股0.01美元
else:
return Decimal'0.005' * order.quantity # 每股0.005美元

async def get_trading_hoursself, symbol: str -> Dict[str, Any]:
"""獲取交易時間"""
# 默認實現，返回標準交易時間
return {
"market_open": "09:30",
"market_close": "16:00",
"timezone": "America/New_York",
"is_open": True # 簡化實現
}

async def get_margin_requirementsself, symbol: str -> Dict[str, Decimal]:
"""獲取保證金要求"""

return {
"initial_margin": Decimal'0.5', # 50%初始保證金
"maintenance_margin": Decimal'0.25', # 25%維持保證金
"day_trading_margin": Decimal'0.25' # 25%日內交易保證金
}