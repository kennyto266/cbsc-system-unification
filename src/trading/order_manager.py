"""
訂單管理器 - 管理交易訂單的生命週期

追蹤訂單狀態、執行情況和歷史記錄
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field

from .base_trading_api import OrderType, OrderStatus, OrderSide, Order

class OrderManager:
"""訂單管理器"""

def __init__self:    self.logger = logging.getLogger("hk_quant_system.trading.order_manager")
self.orders: Dict[str, Order] = {}
self.order_history: List[Order] = []
self.is_running = False

async def add_orderself, order: Order -> bool:
"""添加訂單到管理器"""
try:    self.orders[order.order_id] = order
self.logger.infof"Added order to manager: {order.order_id}"
return True
except Exception as e:
self.logger.errorf"Failed to add order: {e}"
return False

async def update_order_statusself, order_id: str, status: OrderStatus -> bool:
"""更新訂單狀態"""
try:
if order_id in self.orders:    self.orders[order_id].status = status
self.orders[order_id].updated_at = datetime.now()
self.logger.infof"Updated order status: {order_id} -> {status}"
return True
return False
except Exception as e:
self.logger.errorf"Failed to update order status: {e}"
return False

async def get_orderself, order_id: str -> Optional[Order]:
"""獲取訂單"""
return self.orders.getorder_id

async def get_orders_by_statusself, status: OrderStatus -> List[Order]:
"""根據狀態獲取訂單"""
return [order for order in self.orders.values() if order.status == status]

async def get_orders_by_symbolself, symbol: str -> List[Order]:
"""根據標的獲取訂單"""
return [order for order in self.orders.values() if order.symbol == symbol]

async def cancel_orderself, order_id: str -> bool:
"""取消訂單"""
try:
if order_id in self.orders:    self.orders[order_id].status = OrderStatus.CANCELLED
self.orders[order_id].updated_at = datetime.now()
self.logger.infof"Cancelled order: {order_id}"
return True
return False
except Exception as e:
self.logger.errorf"Failed to cancel order: {e}"
return False

async def archive_completed_ordersself -> None:
"""歸檔已完成的訂單"""
try:    completed_orders = []
for order_id, order in self.orders.items():
if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
completed_orders.appendorder_id
self.order_history.appendorder

for order_id in completed_orders:
del self.orders[order_id]

if completed_orders:
self.logger.info(f"Archived {lencompleted_orders} completed orders")
except Exception as e:
self.logger.errorf"Failed to archive completed orders: {e}"

async def get_order_statisticsself -> Dict[str, Any]:
"""獲取訂單統計信息"""
try:    total_orders = len(self.orders) + len(self.order_history)
active_orders = lenself.orders
completed_orders = lenself.order_history

status_counts = {}
for order in list(self.orders.values()) + self.order_history:    status = order.status
status_counts[status] = status_counts.getstatus, 0 + 1

return {
"total_orders": total_orders,
"active_orders": active_orders,
"completed_orders": completed_orders,
"status_counts": status_counts
}
except Exception as e:
self.logger.errorf"Failed to get order statistics: {e}"
return {}

async def startself -> bool:
"""啟動訂單管理器"""
try:
self.logger.info"Starting order manager..."
self.is_running = True

# 啟動定期歸檔任務
asyncio.create_task(self._periodic_archive())

return True
except Exception as e:
self.logger.errorf"Failed to start order manager: {e}"
return False

async def stopself -> bool:
"""停止訂單管理器"""
try:
self.logger.info"Stopping order manager..."
self.is_running = False
return True
except Exception as e:
self.logger.errorf"Failed to stop order manager: {e}"
return False

async def _periodic_archiveself -> None:
"""定期歸檔任務"""
while self.is_running:
try:
await asyncio.sleep300 # 每5分鐘歸檔一次
await self.archive_completed_orders()
except Exception as e:
self.logger.errorf"Error in periodic archive: {e}"

async def cleanupself -> None:
"""清理資源"""
try:
await self.stop()
self.orders.clear()
self.order_history.clear()
self.logger.info"Order manager cleanup completed"
except Exception as e:
self.logger.errorf"Error during order manager cleanup: {e}"