"""
交易服務
管理交易執行和訂單處理
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class OrderStatus(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class TradingService:
    """交易服務"""

    def __init__(self):
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        self.order_history: List[Dict[str, Any]] = []
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False

    async def initialize(self):
        """初始化交易服務"""
        try:
            logger.info("交易服務初始化")
            self.is_initialized = True
            logger.info("交易服務初始化完成")
        except Exception as e:
            logger.error(f"交易服務初始化失敗: {e}")
            raise

    async def health_check(self) -> bool:
        """健康檢查"""
        return self.is_initialized

    async def shutdown(self):
        """關閉交易服務"""
        try:
            logger.info("關閉交易服務...")
            self.is_initialized = False
            logger.info("交易服務已關閉")
        except Exception as e:
            logger.error(f"關閉交易服務時發生錯誤: {e}")

    async def create_order(self, symbol: str, side: OrderSide, order_type: OrderType, quantity: int, price: Optional[float] = None) -> str:
        """創建訂單"""
        order_id = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_orders)}"

        order = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "price": price,
            "status": OrderStatus.PENDING,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        self.active_orders[order_id] = order

        logger.info(f"創建訂單: {order_id}")
        return order_id

    async def cancel_order(self, order_id: str) -> bool:
        """取消訂單"""
        if order_id in self.active_orders:
            self.active_orders[order_id]["status"] = OrderStatus.CANCELLED
            self.active_orders[order_id]["updated_at"] = datetime.now()
            logger.info(f"取消訂單: {order_id}")
            return True
        return False

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """獲取訂單狀態"""
        return self.active_orders.get(order_id)

    async def get_active_orders(self) -> List[Dict[str, Any]]:
        """獲取活躍訂單列表"""
        return list(self.active_orders.values())

    async def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取持倉信息"""
        return self.positions.get(symbol)

    async def update_position(self, symbol: str, quantity: int, avg_price: float) -> None:
        """更新持倉"""
        if symbol in self.positions:
            # 更新現有持倉
            pos = self.positions[symbol]
            new_quantity = pos["quantity"] + quantity
            if new_quantity == 0:
                del self.positions[symbol]
            else:
                pos["quantity"] = new_quantity
                pos["avg_price"] = ((pos["avg_price"] * pos["quantity"]) + (avg_price * quantity)) / new_quantity
                pos["updated_at"] = datetime.now()
        else:
            # 創建新持倉
            self.positions[symbol] = {
                "symbol": symbol,
                "quantity": quantity,
                "avg_price": avg_price,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }